class RouteNotFoundError(Exception):
    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"No route found for path '{path}'")
