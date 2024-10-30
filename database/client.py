import logging
from os import PathLike

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import AbstractContextManager

from .schemas import base, Users

logger = logging.getLogger('database')

class DBClient:
    def __init__(self, url: str | PathLike) -> None:
        self._engine = create_engine(url)
        self._session_maker = sessionmaker(bind=self._engine)

        base.metadata.create_all(self._engine)

        logger.info('Initialized database client...')

    def get_session(self) -> AbstractContextManager[Session]:
        return self._session_maker.begin()

    def get_user(self, uid: int, session: Session) -> Users:
        return session.query(Users).filter(Users.id == uid).first()

    def add_user(self, uid: int, session: Session) -> Users:
        user = Users(id=uid)
        session.add(user)
        return user