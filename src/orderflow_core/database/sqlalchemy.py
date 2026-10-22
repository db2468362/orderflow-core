from collections.abc import AsyncGenerator
from dataclasses import dataclass

from dishka import Scope
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from orderflow_core.di import injectable


@dataclass
class DatabaseConfig:
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    expire_on_commit: bool = False
    autoflush: bool = False


@injectable(scope=Scope.APP)
def get_engine(config: DatabaseConfig) -> AsyncEngine:
    return create_async_engine(
        config.url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        pool_pre_ping=config.pool_pre_ping,
    )


@injectable(scope=Scope.APP)
def get_sessionmaker(
    engine: AsyncEngine,
    config: DatabaseConfig,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=config.expire_on_commit,
        autoflush=config.autoflush,
    )


@injectable(scope=Scope.REQUEST)
async def get_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with sessionmaker() as session:
        yield session
