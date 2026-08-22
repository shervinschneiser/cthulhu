from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.redis import redis_client
from app.gateway import GatewayDispatcher
from app.gateway.constants import SUPPORTED_METHODS
from app.gateway.load_balancer import LoadBalancer
from app.proxy.client import ProxyClient
from app.proxy.exceptions import (
    ProxyTimeoutError,
    UpstreamUnavailableError,
)
from app.proxy.url_builder import build_upstream_url
from app.rate_limit.key import get_rate_limit_key
from app.rate_limit.limiter import RateLimiter
from app.routing import Route, RouteRegistry
from app.routing.exceptions import RouteNotFoundError
from app.routing.resolver import RouteResolver


router = APIRouter(tags=["Gateway"])

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

resolver = RouteResolver(registry)
dispatcher = GatewayDispatcher(resolver)

proxy = ProxyClient()

rate_limiter = RateLimiter(
    redis_client,
    limit=100,
)

load_balancers: dict[str, LoadBalancer] = {
    "/users": LoadBalancer(
        (
            "http://localhost:9000",
            "http://localhost:9001",
        )
    ),
}


@router.api_route(
    "/{path:path}",
    methods=SUPPORTED_METHODS,
)
async def gateway(
    request: Request,
    path: str,
):
    try:
        route = dispatcher.dispatch(f"/{path}")

        rate_limit_key = get_rate_limit_key(
            request,
            route.normalized_path,
        )

        if not await rate_limiter.allow(rate_limit_key):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
            )

        load_balancer = load_balancers.get(route.normalized_path)

        if load_balancer is None:
            raise HTTPException(
                status_code=502,
                detail="No upstream configured",
            )

        upstream = load_balancer.next()

        upstream_url = build_upstream_url(
            upstream,
            path,
        )

        response, stream = await proxy.stream(
            method=request.method,
            url=upstream_url,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() != "host"
            },
            params=dict(request.query_params),
            content=request.stream(),
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

        return StreamingResponse(
            stream,
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
