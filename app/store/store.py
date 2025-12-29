# store/store.py
import os
from logging import Logger
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from store.models import Base
from store.repositories import UsersRepository, QuestionsRepository, PassRepository
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
        self.pass_ = PassRepository(self.engine)

    def init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        Base.metadata.create_all(self.engine)

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
