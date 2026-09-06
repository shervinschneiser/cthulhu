from dataclasses import dataclass

from app.gateway.circuit_registry import CircuitBreakerRegistry


@dataclass(slots=True)
class LoadBalancer:
    upstreams: list[str]
    circuit_registry: CircuitBreakerRegistry
    _index: int = 0

    def next(self) -> str:
        if not self.upstreams:
            raise ValueError("No upstreams configured")

        for _ in range(len(self.upstreams)):
            upstream = self.upstreams[self._index]
            self._index = (self._index + 1) % len(self.upstreams)

            breaker = self.circuit_registry.get(upstream)

            if not breaker.is_open():
                return upstream

        raise RuntimeError("No healthy upstream available")
