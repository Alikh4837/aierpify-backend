# src\database.py
from typing import Annotated, AsyncGenerator, TypeVar, Union

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from src.config import get_setting


# ------------------------------- Database URL ------------------------------- #
def get_database_url() -> str:
    POSTGRES_HOST = get_setting("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = get_setting("POSTGRES_PORT", 5432)
    POSTGRES_DB = get_setting("POSTGRES_DB", "postgres")
    POSTGRES_USER = get_setting("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = get_setting("POSTGRES_PASSWORD", "postgres")

    return f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


# ------------------------------ Database Engine ----------------------------- #
ASYNC_ENGINE: AsyncEngine = create_async_engine(
    url=get_database_url(),
    echo=True,
    future=True,
)

# ----------------------------- Database Session ----------------------------- #
# Create the async session
ASYNC_SESSION = async_sessionmaker(
    ASYNC_ENGINE, class_=AsyncSession, expire_on_commit=False
)

# ---------------------------- Genetic Query Type ---------------------------- #
# TypeVar for generic query types
TQUERY = TypeVar("TQUERY", bound=Union[SelectOfScalar, Select])


# ----------------------------- Database Session ----------------------------- #
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with ASYNC_SESSION() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------- Database Dependency --------------------------- #
DBDep = Annotated[AsyncSession, Depends(get_session)]
