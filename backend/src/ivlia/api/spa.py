"""Serves the built SPA from the package, on the same origin as the API."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"
"""Where `vite build` writes the SPA. Missing in dev with Vite and in tests."""

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        # Nothing leaves the Mac: the page may only talk to ivlia's own API.
        "connect-src 'self'",
        "img-src 'self' data:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)


def built_spa() -> Path | None:
    """The built SPA's folder, or None if it was not built."""
    return STATIC_DIR if (STATIC_DIR / "index.html").is_file() else None


def mount_spa(app: FastAPI, static_dir: Path) -> None:
    """Serve the SPA's files, and its index.html for any other non-API path.

    Routes added before this one, the API's, take precedence.
    """
    index = static_dir / "index.html"
    # Top-level files (favicon) by name, so a path never reaches the disk.
    files = {path.name: path for path in static_dir.iterdir() if path.is_file()}
    if (static_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"))

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return FileResponse(
            files.get(path, index),
            headers={"Content-Security-Policy": CONTENT_SECURITY_POLICY},
        )
