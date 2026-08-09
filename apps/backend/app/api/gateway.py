from fastapi import APIRouter, HTTPException, Request, Response

from app.gateway import GatewayDispatcher
from app.proxy.client import ProxyClient
from app.routing import Route, RouteRegistry
from app.routing.exceptions import RouteNotFoundError
from app.routing.resolver import RouteResolver
from app.proxy.utils import normalize_upstream
from app.proxy.url_builder import build_upstream_url

from app.core.redis import redis_client
from app.rate_limit.limiter import RateLimiter

from app.gateway.constants import SUPPORTED_METHODS

router = APIRouter(tags=["Gateway"])

registry = RouteRegistry()
registry.register(
    Route(
        path="/users",
        upstream="http://localhost:9000",
    )
)

resolver = RouteResolver(registry)
dispatcher = GatewayDispatcher(resolver)

proxy = ProxyClient()
rate_limiter = RateLimiter(redis_client, limit=100)


@router.api_route(
    "/{path:path}",
    methods=SUPPORTED_METHODS,
)
async def gateway(request: Request, path: str):

    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limiter.allow(f"rate-limit:{client_ip}"):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )

    try:
        route = dispatcher.dispatch(f"/{path}")

        remaining_path = path.removeprefix(route.path.lstrip("/"))
        # upstream_url = f"{normalize_upstream(route.upstream)}/{remaining_path.lstrip('/')}"
        upstream_url = build_upstream_url(route.upstream, path)

        response = await proxy.forward(
            method=request.method,
            url=upstream_url,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() != "host"
            },
            params=dict(request.query_params),
            content=await request.body(),
        )

        excluded_headers = {
            "content-length",
            "transfer-encoding",
            "connection",
        }

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in excluded_headers
        }

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=headers,
            media_type=response.headers.get("content-type"),
        )

    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
