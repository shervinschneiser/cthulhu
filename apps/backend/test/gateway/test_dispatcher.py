import pytest

from app.gateway import GatewayDispatcher
from app.routing import Route, RouteRegistry
from app.routing.exceptions import RouteNotFoundError
from app.routing.resolver import RouteResolver


def create_dispatcher() -> GatewayDispatcher:
    registry = RouteRegistry()

    registry.register(
        Route(
            path="/users",
            upstreams=(
                "http://localhost:9000",
                "http://localhost:9001",
            ),
        )
    )

    return GatewayDispatcher(
        RouteResolver(registry),
    )


def test_dispatches_registered_route():
    dispatcher = create_dispatcher()

    route = dispatcher.dispatch("/users")

    assert route.normalized_path == "/users"
    assert route.upstreams == (
        "http://localhost:9000",
        "http://localhost:9001",
    )


def test_raises_route_not_found_error():
    dispatcher = create_dispatcher()

    with pytest.raises(
        RouteNotFoundError,
        match="Route not found: /unknown",
    ):
        dispatcher.dispatch("/unknown")


def test_dispatches_trailing_slash_route():
    dispatcher = create_dispatcher()

    route = dispatcher.dispatch("/users/")

    assert route.normalized_path == "/users"
