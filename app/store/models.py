from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # так как уже DeclarativeBase строчка излишняя
    # __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    # created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class UsersTable(Base):
    __tablename__ = "Users"

    # телеграм id
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    # аген?
    permissions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)


class RequestTable(Base):
    __tablename__ = "Request"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Users.user_id"), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Question.id"), nullable=True)
    # для ии
    session_id: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parent_id: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class QuestionsTable(Base):
    __tablename__ = "Question"

    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("Users.user_id"), nullable=True)
    author_type: Mapped[str] = mapped_column(Text, nullable=False, default="user")
    text: Mapped[str] = mapped_column(Text, nullable=True)
    previous_question: Mapped[int] = mapped_column(
        Integer, ForeignKey("Question.id"), nullable=True)
    request: Mapped[int] = mapped_column(
        Integer, ForeignKey("Request.id"), nullable=False)
