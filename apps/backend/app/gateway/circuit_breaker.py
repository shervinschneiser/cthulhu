from dataclasses import dataclass


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    failures: int = 0
    opened_at: float | None = None

    def record_failure(self) -> None:
        self.failures += 1

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def is_open(self, now: float) -> bool:
        if self.opened_at is None:
            return False

        return now - self.opened_at < self.recovery_timeout
