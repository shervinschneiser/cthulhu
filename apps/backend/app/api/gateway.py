from fastapi import APIRouter, HTTPException

from app.gateway import GatewayDispatcher
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


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def gateway(path: str):
    try:
        route = dispatcher.dispatch(f"/{path}")

        return {
            "matched": True,
            "path": route.path,
            "upstream": route.upstream,
        }

    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
