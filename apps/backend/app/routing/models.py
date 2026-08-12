from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Route:
    path: str
    upstreams: tuple[str, ...]

    @property
    def normalized_path(self) -> str:
        if self.path == "/":
            return "/"

        return self.path.rstrip("/")

    @property
    def upstream(self) -> str:
        return self.upstreams[0]

    def __post_init__(self) -> None:
        if not self.path.startswith("/"):
            raise ValueError("Route path must start with '/'.")

        if not self.upstreams:
            raise ValueError("Route must have at least one upstream.")
