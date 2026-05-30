# store/store.py
import os
from logging import Logger
import re
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session

from store.models import Base
from store.repositories import UsersRepository, QuestionsRepository, RequestRepository
from setup_logger import setup_logger

def _fk_pragma_on_connect(dbapi_con, con_record):
    cur = dbapi_con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.close()


class Store:
    def __init__(self, db_path: str, logger: Optional[Logger] = None) -> None:
        self.logger = logger or setup_logger(__name__)
        
        self.db_path = db_path
        self.db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(
            self.db_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        event.listen(self.engine, "connect", _fk_pragma_on_connect)

        # репозитории
        self.user = UsersRepository(self.engine)
        self.question = QuestionsRepository(self.engine)
        self.request = RequestRepository(self.engine)

    def init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        Base.metadata.create_all(self.engine)
        self._migrate_db()

    def _migrate_db(self) -> None:
        inspector = inspect(self.engine)
        if "Question" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("Question")}
        missing_columns = {
            "telegram_chat_id": "INTEGER",
            "telegram_message_id": "INTEGER",
            "content_type": "TEXT",
        }
        columns_to_add = [
            (name, column_type)
            for name, column_type in missing_columns.items()
            if name not in existing_columns
        ]
        if not columns_to_add:
            return

        with self.engine.begin() as connection:
            for column_name, column_type in columns_to_add:
                connection.execute(text(f'ALTER TABLE "Question" ADD COLUMN {column_name} {column_type}'))
        self.logger.info(
            "Database migrated: added Question columns %s",
            ", ".join(column_name for column_name, _ in columns_to_add),
        )

    def drop_all(self) -> None:
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def session_scope(self):
        with Session(self.engine) as s:
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise
