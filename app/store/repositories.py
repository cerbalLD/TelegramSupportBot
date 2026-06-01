# store/repositories.py
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from store.models import Base, UsersTable, RequestTable, QuestionsTable

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    def __init__(self, engine: Engine, model: Type[ModelT]):
        self.engine = engine
        self.model = model

    # --- базовые CRUD ---
    def create(self, **fields) -> int:
        with Session(self.engine) as s:
            obj = self.model(**fields)  # type: ignore[arg-type]
            s.add(obj)
            s.commit()
            s.refresh(obj)
            return obj.id

    def get(self, id: int) -> Optional[ModelT]:
        with Session(self.engine) as s:
            return s.get(self.model, id)

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[Any] = None,
        **filters: Any,
    ) -> List[ModelT]:
        with Session(self.engine) as s:
            q = s.query(self.model)

            # простые фильтры model.field == value
            for field_name, value in filters.items():
                if value is None:
                    continue
                q = q.filter(getattr(self.model, field_name) == value)

            if order_by is None:
                order_by = self.model.id  # type: ignore[attr-defined]

            q = q.order_by(order_by)
            return q.offset(offset).limit(limit).all()

    def update(self, id: int, **fields) -> bool:
        with Session(self.engine) as s:
            obj = s.get(self.model, id)
            if not obj:
                return False

            for field_name, value in fields.items():
                if value is not None:
                    setattr(obj, field_name, value)

            s.commit()
            return True

    def delete(self, id: int) -> bool:
        with Session(self.engine) as s:
            obj = s.get(self.model, id)
            if not obj:
                return False
            s.delete(obj)
            s.commit()
            return True


class UsersRepository(Repository[UsersTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, UsersTable)

    def get_by_user_id(self, user_id: int) -> Optional[UsersTable]:
        """Находит пользователя по telegram user_id"""
        with Session(self.engine) as s:
            return s.query(UsersTable).filter(
                UsersTable.user_id == user_id
            ).first()

    def set_permissions_by_user_id(self, user_id: int, permissions: int) -> UsersTable:
        with Session(self.engine) as s:
            user = s.query(UsersTable).filter(
                UsersTable.user_id == user_id).first()
            if user is None:
                user = UsersTable(user_id=user_id, permissions=permissions)
                s.add(user)
            else:
                user.permissions = permissions
            s.commit()
            s.refresh(user)
            return user
        
    def list_operators(self) -> List[UsersTable]:
        with Session(self.engine) as s:
            return s.query(UsersTable).filter(UsersTable.permissions > 0).all()


class RequestRepository(Repository[RequestTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, RequestTable)

    def get_by_user_id(self, user_id: int) -> Optional[RequestTable]:
        with Session(self.engine) as s:
            return s.query(RequestTable).filter(
                RequestTable.user_id == user_id
            ).order_by(RequestTable.id.desc()).first()

    def list_open(self, *, limit: int = 10, offset: int = 0) -> List[RequestTable]:
        with Session(self.engine) as s:
            return (
                s.query(RequestTable)
                .filter(RequestTable.status != 3)
                .order_by(RequestTable.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    def count_need_operator(self) -> int:
        with Session(self.engine) as s:
            return s.query(RequestTable).filter(
                RequestTable.status > 0,
                RequestTable.status != 3,
            ).count()

    def delete_with_questions(self, request_id: int) -> bool:
        with Session(self.engine) as s:
            request = s.get(RequestTable, request_id)
            if not request:
                return False

            question_ids = [
                row.id
                for row in s.query(QuestionsTable.id)
                .filter(QuestionsTable.request == request_id)
                .all()
            ]
            if question_ids:
                s.query(RequestTable).filter(
                    RequestTable.last_message_id.in_(question_ids)
                ).update({RequestTable.last_message_id: None}, synchronize_session=False)
                s.query(QuestionsTable).filter(
                    QuestionsTable.previous_question.in_(question_ids)
                ).update({QuestionsTable.previous_question: None}, synchronize_session=False)
                s.query(QuestionsTable).filter(
                    QuestionsTable.id.in_(question_ids)
                ).delete(synchronize_session=False)

            s.delete(request)
            s.commit()
            return True


class QuestionsRepository(Repository[QuestionsTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, QuestionsTable)

    def ai_count_by_request(self, request_id: int) -> int:
        with Session(self.engine) as s:
            return s.query(QuestionsTable).filter(
                QuestionsTable.request == request_id,
                QuestionsTable.user_id.is_(None),
            ).count()

    def list_by_request(self, request_id: int) -> List[QuestionsTable]:
        with Session(self.engine) as s:
            return (
                s.query(QuestionsTable)
                .filter(QuestionsTable.request == request_id)
                .order_by(QuestionsTable.id)
                .all()
            )
