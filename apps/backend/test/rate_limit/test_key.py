from fastapi import Request

from app.rate_limit.key import get_rate_limit_key


def create_request(
    *,
    headers: dict[str, str] | None = None,
    client: tuple[str, int] | None = ("127.0.0.1", 5000),
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in (headers or {}).items()
        ],
        "client": client,
        "scheme": "http",
        "server": ("localhost", 8000),
    }

    return Request(scope)


def test_uses_api_key_when_available():
    request = create_request(
        headers={"x-api-key": "abc123"},
    )

    assert get_rate_limit_key(request) == "rate-limit:api-key:abc123"


def test_uses_client_ip_when_api_key_is_missing():
    request = create_request(
        client=("192.168.1.10", 5000),
    )

    assert get_rate_limit_key(request) == "rate-limit:ip:192.168.1.10"


def test_uses_unknown_ip_when_client_is_missing():
    request = create_request(client=None)

    assert get_rate_limit_key(request) == "rate-limit:ip:unknown"


def test_includes_route_path():
    request = create_request(
        headers={"x-api-key": "abc123"},
    )

    assert get_rate_limit_key(request, "/users") == "rate-limit:/users:api-key:abc123"


def test_different_routes_produce_different_keys():
    request = create_request(
        headers={"x-api-key": "abc123"},
    )

    users_key = get_rate_limit_key(request, "/users")
    orders_key = get_rate_limit_key(request, "/orders")

    assert users_key != orders_key
