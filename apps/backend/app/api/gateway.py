from fastapi import APIRouter, HTTPException, Request, Response

from app.gateway import GatewayDispatcher
from app.proxy.client import ProxyClient
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


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def gateway(request: Request, path: str):
    try:
        route = dispatcher.dispatch(f"/{path}")

        upstream_url = f"{route.upstream.rstrip('/')}/{path}"

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
