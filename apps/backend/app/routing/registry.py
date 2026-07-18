from app.routing.models import Route


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def register(self, route: Route) -> None:
        self._routes.append(route)

    def all(self) -> list[Route]:
        return self._routes.copy()
