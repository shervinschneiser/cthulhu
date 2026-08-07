def build_upstream_url(upstream: str, path: str) -> str:
    return f"{upstream.rstrip('/')}/{path.lstrip('/')}"