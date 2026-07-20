from app.routing.models import Route
from app.routing.registry import RouteRegistry


class RouteResolver:
    def __init__(self, registry: RouteRegistry) -> None:
        self._registry = registry

    def resolve(self, path: str) -> Route | None:
        matched_route: Route | None = None

        for route in self._registry.all():
            if path == route.path or path.startswith(f"{route.path}/"):
                if matched_route is None or len(route.path) > len(matched_route.path):
                    matched_route = route

        return matched_route
