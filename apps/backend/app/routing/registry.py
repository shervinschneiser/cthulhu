from app.routing.models import Route


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def register(self, route: Route) -> None:
        if any(item.path == route.path for item in self._routes):
            raise ValueError(f"Route '{route.path}' already exists.")

        self._routes.append(route)

    def all(self) -> list[Route]:
        return self._routes.copy()
