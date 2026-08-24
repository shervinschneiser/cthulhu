from app.gateway.circuit_breaker import CircuitBreaker


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, upstream: str) -> CircuitBreaker:
        if upstream not in self._breakers:
            self._breakers[upstream] = CircuitBreaker()

        return self._breakers[upstream]

    def has(self, upstream: str) -> bool:
        return upstream in self._breakers

    def all(self) -> dict[str, CircuitBreaker]:
        return self._breakers.copy()
