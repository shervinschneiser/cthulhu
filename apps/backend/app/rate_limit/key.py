from fastapi import Request


def get_rate_limit_key(
    request: Request,
    route_path: str | None = None,
) -> str:
    api_key = request.headers.get("x-api-key")

    if api_key:
        client = f"api-key:{api_key}"
    elif request.client:
        client = f"ip:{request.client.host}"
    else:
        client = "ip:unknown"

    if route_path:
        return f"rate-limit:{route_path}:{client}"

    return f"rate-limit:{client}"
