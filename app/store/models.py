# store/models.py
from typing import Optional
from datetime import datetime

from sqlalchemy import Integer, TIMESTAMP, text, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    # так как уже DeclarativeBase строчка излишняя
    # __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    
class UsersTable(Base):
    __tablename__ = "Users"

    # телеграм id
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    # аген?
    is_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    # алмин?
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
class QuestionsTable(Base):
    __tablename__ = "Questions"

    # кто спросил
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=False)
    # на какое сообщение отвечать
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # в очереди на оператора?
    is_need_operator: Mapped[bool] = mapped_column(Boolean, default=False)
    # текст ответа
    answer: Mapped[str] = mapped_column(Text, nullable=True)
    # когда спросили
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    # когда закрыли
    answered_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    
class PassTable(Base):
    __tablename__ = "Passes"
    
    # название
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # активирован?
    is_actvated: Mapped[bool] = mapped_column(Boolean, default=False)
    # кто активировал
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"), nullable=True)
    
    