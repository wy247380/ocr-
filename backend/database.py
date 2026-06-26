"""
数据库引擎 + Session 管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase

from .config import DATABASE_URL

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if "sqlite" in DATABASE_URL:
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=not DATABASE_URL.startswith("sqlite"),
            echo=False,
            connect_args=connect_args,
        )
    return _engine


class Base(DeclarativeBase):
    pass


def init_db():
    from .models import Base as ModelBase
    ModelBase.metadata.create_all(get_engine())


def get_session() -> Session:
    return Session(get_engine())
