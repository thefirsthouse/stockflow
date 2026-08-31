from typing import AsyncGenerator

import sqlalchemy.types as types
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(settings.database_url, echo=settings.sql_echo)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


class Base(DeclarativeBase):
    pass


class ChoiceType(types.TypeDecorator):
    class ChoiceType(types.TypeDecorator):
    """
    SQLAlchemy type that stores a string key in the database but returns
    its corresponding human-readable value in Python.

    Maps database keys to display values via a choices dictionary.
    """

    impl = types.String

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)
    

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.itertimes() if v == value][0]
    

    def process_result_value(self, value, dialect):
        return self.choices[value]
