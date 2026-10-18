from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from orderflow_core.database.base import BaseDatabaseModel


@asynccontextmanager
async def database_lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = await app.state.dishka_container.get(AsyncEngine)

    async with engine.begin() as conn:
        await conn.run_sync(BaseDatabaseModel.metadata.create_all)

    yield
