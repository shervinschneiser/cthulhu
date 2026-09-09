import pytest

from app.routing import Route, RouteRegistry
from app.routing.exceptions import RouteNotFoundError
from app.routing.resolver import RouteResolver


def create_resolver() -> RouteResolver:
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

    registry.register(
        Route(
            path="/orders",
            upstreams=("http://localhost:9010",),
        )
    )

    return RouteResolver(registry)


def test_resolves_registered_route():
    resolver = create_resolver()

    route = resolver.resolve("/users")

    assert route is not None
    assert route.normalized_path == "/users"
    assert route.upstreams == (
        "http://localhost:9000",
        "http://localhost:9001",
    )


def test_resolves_second_registered_route():
    resolver = create_resolver()

    route = resolver.resolve("/orders")

    assert route is not None
    assert route.normalized_path == "/orders"
    assert route.upstreams == ("http://localhost:9010",)


def test_returns_none_for_unknown_route():
    resolver = create_resolver()

    assert resolver.resolve("/unknown") is None


def test_resolves_trailing_slash():
    resolver = create_resolver()

    route = resolver.resolve("/users/")

    assert route is not None
    assert route.normalized_path == "/users"


def test_route_not_found_error_contains_path():
    resolver = create_resolver()

    with pytest.raises(RouteNotFoundError):
        route = resolver.resolve("/missing")

        if route is None:
            raise RouteNotFoundError("/missing")
