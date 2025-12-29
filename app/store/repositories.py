# store/repositories.py
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from store.models import Base, UsersTable, QuestionsTable, PassTable

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

class QuestionsRepository(Repository[QuestionsTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, QuestionsTable)
        
    def get_last_question_by_date(self, user_id: int) -> Optional[QuestionsTable]:
        with Session(self.engine) as s:
            return s.query(QuestionsTable).filter(user_id == user_id).order_by(QuestionsTable.created_at.desc()).first()
        
    def set_need_operator_for_last_question(self, user_id: int, need_operator: bool = True) -> bool:
        with Session(self.engine) as s:
            obj = s.query(QuestionsTable).filter(user_id == user_id).order_by(QuestionsTable.created_at.desc()).first()
            if not obj:
                return False
            obj.is_need_operator = need_operator
            s.commit()
            return True
    
class PassRepository(Repository[PassTable]):
    def __init__(self, engine: Engine):
        super().__init__(engine, PassTable)
        
    def get_by_name(self, name: str) -> Optional[PassTable]:
        with Session(self.engine) as s:
            return s.query(PassTable).filter(PassTable.name == name).first()
        
    def get_by_user_id(self, user_id: int) -> Optional[PassTable]:
        with Session(self.engine) as s:
            return s.query(PassTable).filter(PassTable.user_id == user_id).first()