from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Route:
    path: str
    upstream: str

    @property
    def normalized_path(self) -> str:
        if self.path == "/":
            return "/"

        return self.path.rstrip("/")