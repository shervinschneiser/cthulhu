from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Route:
    path: str
    upstream: str
