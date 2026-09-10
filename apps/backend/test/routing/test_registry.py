from app.routing import Route, RouteRegistry


def create_registry() -> RouteRegistry:
    registry = RouteRegistry()

    registry.register(
        Route(
            path="/users",
            upstreams=("http://localhost:9000",),
        )
    )

    return registry


def test_get_returns_registered_route():
    registry = create_registry()

    route = registry.get("/users")

    assert route is not None
    assert route.normalized_path == "/users"


def test_get_returns_none_for_unknown_route():
    registry = create_registry()

    assert registry.get("/unknown") is None


def test_registered_route_preserves_upstreams():
    registry = create_registry()

    route = registry.get("/users")

    assert route is not None
    assert route.upstreams == ("http://localhost:9000",)


def test_register_replaces_existing_route():
    registry = create_registry()

    registry.register(
        Route(
            path="/users",
            upstreams=("http://localhost:9010",),
        )
    )

    route = registry.get("/users")

    assert route is not None
    assert route.upstreams == ("http://localhost:9010",)
