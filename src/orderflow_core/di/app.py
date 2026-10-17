from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka import Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from orderflow_core.di.registry import DIRegistry, default_registry


def setup_di(
    app: FastAPI,
    *providers: Provider,
    registry: DIRegistry = default_registry,
) -> None:
    if getattr(app.state, 'di_initialized', False):
        message = 'DI is already initialized'
        raise RuntimeError(message)

    container = make_async_container(
        registry.build_provider(),
        *providers,
    )

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            async with original_lifespan(app):
                yield
        finally:
            await container.close()

    app.router.lifespan_context = lifespan

    setup_dishka(container, app)
    app.state.di_initialized = True
