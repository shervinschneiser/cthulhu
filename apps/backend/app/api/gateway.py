from fastapi import APIRouter, HTTPException, Request, Response

from app.core.redis import redis_client
from app.gateway import GatewayDispatcher
from app.gateway.constants import SUPPORTED_METHODS
from app.proxy.client import ProxyClient
from app.proxy.exceptions import (
    ProxyTimeoutError,
    UpstreamUnavailableError,
)
from app.proxy.url_builder import build_upstream_url
from app.rate_limit.limiter import RateLimiter
from app.routing import Route, RouteRegistry
from app.routing.exceptions import RouteNotFoundError
from app.routing.resolver import RouteResolver


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

        upstream_url = build_upstream_url(
            route.upstream,
            path,
        )

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

    except ProxyTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Upstream request timed out",
        ) from exc

    except UpstreamUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail="Upstream service unavailable",
        ) from exc
