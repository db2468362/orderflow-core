# orderflow-core

`orderflow-core` is a foundational library for the **OrderFlow** microservice ecosystem. It provides reusable infrastructure components for database models, dependency injection, exception handling, and FastAPI integration.

The library reduces boilerplate code and ensures consistent infrastructure patterns across backend services.

---

## Features

- **Domain-Driven Exception Hierarchy**: Pure Python application exceptions decoupled from HTTP infrastructure.
- **Automated FastAPI Exception Handling**: Maps application exceptions to HTTP status codes such as `404 Not Found` and `409 Conflict`.
- **Request Validation Handling**: Converts FastAPI request validation errors into standardized JSON responses.
- **Consistent API Error Responses**: Provides a unified JSON error format across microservices.
- **Simplified Dependency Injection**: Provides a declarative `@injectable` decorator built on top of Dishka.
- **Automatic Dependency Registration**: Collects decorated dependencies into a centralized registry.
- **Dependency Scope Management**: Supports Dishka scopes such as `Scope.APP` and `Scope.REQUEST`.
- **FastAPI Integration**: Automatically initializes and connects the Dishka dependency injection container.
- **Automatic Resource Cleanup**: Ensures proper container shutdown and resource disposal.
- **Shared SQLAlchemy Base Model**: Provides common `created_at` and `updated_at` fields for database models.
- **Database Lifespan Management**: Automatically creates missing database tables during FastAPI startup.

---

## Dependency Injection

`orderflow-core` provides a lightweight abstraction over **Dishka**, simplifying dependency registration and container initialization while preserving its lifecycle management capabilities.

### Registering Dependencies

Use the `@injectable` decorator to register classes directly in the dependency injection container.

```python
from dishka import Scope
from sqlalchemy.ext.asyncio import AsyncSession

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


app = FastAPI()

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

## Database

`orderflow-core` provides reusable SQLAlchemy infrastructure for OrderFlow microservices.

It includes:

- A shared declarative base model.
- Automatically managed timestamp columns.
- A FastAPI lifespan context manager for database initialization.

### Base Database Model

All SQLAlchemy models can inherit from `BaseDatabaseModel`.

```python
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseDatabaseModel(DeclarativeBase):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

The base model provides two common timestamp fields:

| Field | Description |
|---|---|
| `created_at` | Automatically initialized when a record is created. |
| `updated_at` | Automatically initialized on creation and updated during SQLAlchemy UPDATE operations. |

Both fields use timezone-aware PostgreSQL timestamps (`TIMESTAMP WITH TIME ZONE`).

**Note:** `updated_at` is automatically updated by SQLAlchemy when an UPDATE statement is executed without explicitly providing a value for the column. Direct SQL updates outside SQLAlchemy do not automatically trigger this behavior.

### Defining Database Models

Import `BaseDatabaseModel` and inherit from it.

```python
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from orderflow_core.database import BaseDatabaseModel


class Category(BaseDatabaseModel):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )

    description: Mapped[str] = mapped_column(
        String(255),
    )
```

The resulting table automatically includes the `created_at` and `updated_at` columns.

### Database Lifespan

The library provides `database_lifespan` for automatically creating missing database tables during application startup.

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from orderflow_core.database.base import BaseDatabaseModel


@asynccontextmanager
async def database_lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = await app.state.dishka_container.get(AsyncEngine)

    async with engine.begin() as conn:
        await conn.run_sync(
            BaseDatabaseModel.metadata.create_all
        )

    yield
```

The lifespan:

1. Retrieves the registered `AsyncEngine` from the Dishka container.
2. Opens a database connection.
3. Creates missing tables registered in SQLAlchemy metadata.
4. Completes database initialization before the application starts accepting requests.

**Important:** `create_all()` creates missing tables but does not update existing table structures. Schema modifications require database migrations or manual changes.

### FastAPI Application Setup

A microservice can use the shared database lifespan directly.

```python
from fastapi import FastAPI

from orderflow_core.database import database_lifespan
from orderflow_core.di import setup_di
from orderflow_core.exceptions import register_exception_handlers

from app.handlers.categories import router as category_router
from app.handlers.products import router as product_router

# Import dependency registrations and SQLAlchemy models
# before application initialization.
from app import dependencies, models  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(lifespan=database_lifespan)

    app.include_router(product_router)
    app.include_router(category_router)

    register_exception_handlers(app)
    setup_di(app)

    return app


app = create_app()
```

**Note:** All SQLAlchemy models must be imported before executing `metadata.create_all()` to ensure their tables are registered.

Each independently running microservice maintains its own SQLAlchemy metadata in its Python process, even when using the same shared base class.

---

## Exception Handling

`orderflow-core` provides a centralized exception hierarchy and FastAPI exception handlers.

### Application Exceptions

Application exceptions are independent of FastAPI and HTTP infrastructure.

```python
from orderflow_core.exceptions import (
    ApplicationError,
    ConflictError,
    NotFoundError,
)
```

Available exceptions:

| Exception | Default HTTP Status |
|---|---|
| `ApplicationError` | `500 Internal Server Error` |
| `NotFoundError` | `404 Not Found` |
| `ConflictError` | `409 Conflict` |

Example:

```python
async def get_product_by_id(self, product_id: int):
    product = await self.product_dao.get_product_by_id(product_id)

    if product is None:
        raise NotFoundError(
            f"Product with ID {product_id} not found"
        )

    return product
```

### Registering Exception Handlers

Register the built-in FastAPI exception handlers during application initialization.

```python
from fastapi import FastAPI

from orderflow_core.exceptions import register_exception_handlers


app = FastAPI()

register_exception_handlers(app)
```

### Standardized Error Responses

Application exceptions are converted into a consistent JSON format.

Example response:

```json
{
  "error": "NotFoundError",
  "message": "Product with ID 123 not found"
}
```

HTTP status: `404 Not Found`.

### Request Validation Errors

FastAPI request validation errors can also be mapped into the unified error response format.

For example, if a Pydantic field requires at least three characters and receives a shorter string:

```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "details": [
    {
      "field": "body.description",
      "message": "String should have at least 3 characters",
      "type": "string_too_short"
    }
  ]
}
```

HTTP status: `422 Unprocessable Entity`.

Validation error details include:

| Field | Description |
|---|---|
| `field` | Location of the invalid value. |
| `message` | Human-readable validation error. |
| `type` | Pydantic validation error identifier. |

This handler is registered through `register_exception_handlers()` when request validation handling is included in the library implementation.

### Custom Exception Mapping

Custom application exceptions can be mapped to specific HTTP status codes.

```python
from http import HTTPStatus

from orderflow_core.exceptions import (
    ApplicationError,
    register_exception_handlers,
)


class BusinessRuleError(ApplicationError):
    message = "Business rule violation"


register_exception_handlers(
    app,
    custom_map={
        BusinessRuleError: HTTPStatus.BAD_REQUEST,
    },
)
```

This allows each microservice to extend exception handling without modifying the shared library.

---

## Package Structure

```text
orderflow_core/
├── database/
│   ├── __init__.py
│   ├── base.py
│   └── lifespan.py
├── di/
│   └── ...
└── exceptions/
    ├── __init__.py
    ├── base.py
    └── handlers.py
```

---

## Architecture Principles

The library follows several design principles:

- **Reusability**: Shared infrastructure is implemented once and reused across microservices.
- **Separation of Concerns**: Domain exceptions remain independent of HTTP-specific handling.
- **Dependency Injection**: Services declare dependencies explicitly rather than constructing them manually.
- **Lifecycle Management**: Application resources are managed through Dishka scopes and FastAPI lifespan integration.
- **Consistency**: Database conventions and API error responses follow common standards.
- **Service Independence**: Each microservice owns its business models, database, and application-specific logic.

`orderflow-core` provides common infrastructure without introducing dependencies between individual OrderFlow business services.
