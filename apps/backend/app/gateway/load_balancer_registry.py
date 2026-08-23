from app.gateway.load_balancer import LoadBalancer
from app.routing.models import Route


class LoadBalancerRegistry:
    def __init__(self) -> None:
        self._balancers: dict[str, LoadBalancer] = {}

    def get(self, route: Route) -> LoadBalancer:
        path = route.normalized_path

        if path not in self._balancers:
            self._balancers[path] = LoadBalancer(list(route.upstreams))

        return self._balancers[path]
