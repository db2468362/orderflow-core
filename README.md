# orderflow-core

`orderflow-core` is the core foundational library for the **OrderFlow** microservice ecosystem. It enforces Clean Architecture principles, unified error handling, standardized API responses, and dependency injection across all backend services.

---

## Features

- **Domain-Driven Exception Hierarchy**: Pure Python domain exceptions decoupled from HTTP infrastructure.
- **Automated FastAPI Exception Handler**: Maps domain exception categories into proper HTTP status codes (`404 Not Found`, `409 Conflict`, `400 Bad Request`).
- **Consistent API Error Responses**: Guarantees a standardized JSON structure for all application errors across all microservices.
- **Simplified Dependency Injection**: Provides a declarative `@injectable` decorator built on top of Dishka for registering classes and factory functions.
- **Automatic Dependency Registration**: Collects decorated dependencies into a centralized registry, eliminating repetitive Dishka provider declarations.
- **Dependency Scope Management**: Supports explicit Dishka scopes such as `Scope.APP` and `Scope.REQUEST`.
- **FastAPI Integration**: Automatically initializes and connects the Dishka dependency injection container to FastAPI.
- **Automatic Resource Cleanup**: Integrates with the FastAPI lifespan to ensure proper container shutdown and resource disposal.

---

## Dependency Injection

`orderflow-core` provides a lightweight abstraction over **Dishka**, simplifying dependency registration and container initialization while preserving its lifecycle management capabilities.

### Registering Dependencies

Use the `@injectable` decorator to register classes directly in the dependency injection container.

```python
from dishka import Scope
from orderflow_core.di import injectable


@injectable(scope=Scope.REQUEST)
class ProductDAO:
    def __init__(self, session: AsyncSession):
        self.session = session


@injectable(scope=Scope.REQUEST)
class ProductService:
    def __init__(self, product_dao: ProductDAO):
        self.product_dao = product_dao
```

Dependencies are automatically resolved by Dishka based on constructor type annotations.

### Registering Factory Functions

The `@injectable` decorator also supports synchronous, asynchronous, and generator-based factory functions.

```python
from collections.abc import AsyncIterator

from dishka import Scope
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from orderflow_core.di import injectable


@injectable(scope=Scope.APP)
async def get_engine(
    config: Config,
) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(config.database_url)

    try:
        yield engine
    finally:
        await engine.dispose()
```

Generator-based dependencies support automatic resource cleanup when their corresponding Dishka scope is closed.

### Dependency Scopes

Dependencies must explicitly declare their lifecycle scope.

| Scope | Description |
|---|---|
| `Scope.APP` | A single dependency instance shared throughout the application lifecycle. |
| `Scope.REQUEST` | A dependency instance scoped to an individual request. |

### FastAPI Integration

Initialize dependency injection using the `setup_di()` function.

```python
from fastapi import FastAPI

from orderflow_core.di import setup_di


app = FastAPI(lifespan=lifespan)

setup_di(app)
```

The integration automatically:

- Collects registered dependencies from the dependency registry.
- Builds and initializes the Dishka asynchronous container.
- Connects the container to FastAPI.
- Preserves the application's existing lifespan.
- Closes the container during application shutdown.

**Note:** Modules containing `@injectable` dependencies must be imported before calling `setup_di()` to ensure their registration.

### Using Dependencies in FastAPI

Registered dependencies can be injected into FastAPI endpoints using Dishka's native integration.

```python
from dishka.integrations.fastapi import FromDishka, inject


@router.get("/products")
@inject
async def get_products(
    service: FromDishka[ProductService],
):
    return await service.get_products()
```

Dishka automatically resolves the dependency graph and manages request-scoped instances throughout the request lifecycle.

---