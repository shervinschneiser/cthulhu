from app.routing.models import Route
from app.routing.registry import RouteRegistry


class RouteResolver:
    def __init__(self, registry: RouteRegistry) -> None:
        self._registry = registry

    def resolve(self, path: str) -> Route | None:
        for route in self._registry.all():
            if route.path == path:
                return route

        return None
