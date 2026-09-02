from enum import StrEnum
from time import monotonic


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at: float | None = None
        self._half_open_request_in_flight = False

    def record_failure(self) -> None:
        self._half_open_request_in_flight = False
        self.failures += 1

        if self.state is CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.opened_at = monotonic()
            return

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = monotonic()

    def record_success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self._half_open_request_in_flight = False

    def is_open(self) -> bool:
        if self.state is not CircuitState.OPEN:
            return False

        if self.opened_at is None:
            return False

        if monotonic() - self.opened_at >= self.recovery_timeout:
            self.state = CircuitState.HALF_OPEN
            return False

        return True

    def allow_request(self) -> bool:
        if self.state is CircuitState.CLOSED:
            return True

        if self.state is CircuitState.OPEN:
            if self.is_open():
                return False

        if self.state is CircuitState.HALF_OPEN:
            if self._half_open_request_in_flight:
                return False

            self._half_open_request_in_flight = True
            return True

        return False
