from fastapi import Request


def get_rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key")

    if api_key:
        return f"api-key:{api_key}"

    if request.client:
        return f"ip:{request.client.host}"

    return "ip:unknown"
