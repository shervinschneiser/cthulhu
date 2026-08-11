from dataclasses import dataclass


@dataclass(slots=True)
class LoadBalancer:
    upstreams: list[str]
    _index: int = 0

    def next(self) -> str:
        if not self.upstreams:
            raise ValueError("No upstreams configured")

        upstream = self.upstreams[self._index]
        self._index = (self._index + 1) % len(self.upstreams)

        return upstream
