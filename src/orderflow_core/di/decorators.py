from collections.abc import Callable

from dishka import Scope

from orderflow_core.di.registry import default_registry


def injectable[T](
    *,
    scope: Scope,
) -> Callable[[T], T]:
    def decorator(dependency: T) -> T:
        return default_registry.register(dependency, scope)

    return decorator
