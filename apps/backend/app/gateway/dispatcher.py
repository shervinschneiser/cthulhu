from app.routing.models import Route
from app.routing.resolver import RouteResolver


class GatewayDispatcher:
    def __init__(self, resolver: RouteResolver) -> None:
        self._resolver = resolver

    def dispatch(self, path: str) -> Route | None:
        return self._resolver.resolve(path)
