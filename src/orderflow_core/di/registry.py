from dishka import Provider, Scope


def validate_dependency(dependency: object) -> None:
    if not callable(dependency):
        message = 'Dependency must be callable'
        raise TypeError(message)


class DIRegistry:
    def __init__(self) -> None:
        self._dependencies: dict[object, Scope] = {}

    def register[T](
        self,
        dependency: T,
        scope: Scope,
    ) -> T:
        validate_dependency(dependency)

        if dependency in self._dependencies:
            message = f'Dependency {dependency!r} is already registered'
            raise ValueError(message)

        self._dependencies[dependency] = scope
        return dependency

    def build_provider(self) -> Provider:
        provider = Provider()

        for dependency, scope in self._dependencies.items():
            if not callable(dependency):
                message = f'Dependency {dependency!r} must be callable'
                raise TypeError(message)

            provider.provide(dependency, scope=scope)

        return provider


default_registry = DIRegistry()
