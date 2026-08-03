from app.routing.models import Route


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def exists(self, path: str) -> bool:
        return any(route.path == path for route in self._routes)

    def register(self, route: Route) -> None:
        if self.exists(route.path):
            raise ValueError(f"Route '{route.path}' already exists.")

        self._routes.append(route)

    def find(self, path: str) -> Route | None:
        return next(
            (route for route in self._routes if route.path == path),
            None,
        )

    def count(self) -> int:
        return len(self._routes)

    def remove(self, path: str) -> None:
        self._routes = [route for route in self._routes if route.path != path]

    def all(self) -> list[Route]:
        return self._routes.copy()
