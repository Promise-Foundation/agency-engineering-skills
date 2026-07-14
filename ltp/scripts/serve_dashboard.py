#!/usr/bin/env python3
"""Serve an ltp model through a local, read-only dashboard."""

from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import sys
import threading
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import Optional
from urllib.parse import unquote, urlsplit


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


@dataclass(frozen=True)
class DashboardPaths:
    project: Path
    dashboard: Path  # ltp/generated/dashboard-model.json (produced by `ltp sync`)
    static: Path


def _is_loopback(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_bind_host(host: str, allow_network: bool) -> None:
    if not _is_loopback(host) and not allow_network:
        raise ValueError(
            f"Refusing to bind to {host!r}. Use --allow-network only when network exposure is intentional."
        )


def resolve_paths(project: Path, static: Optional[Path] = None) -> DashboardPaths:
    project = project.expanduser().resolve(strict=True)
    if not project.is_dir():
        raise ValueError(f"Project path is not a directory: {project}")
    dashboard = project / "ltp" / "generated" / "dashboard-model.json"
    if not dashboard.is_file():
        raise FileNotFoundError(
            f"Missing {dashboard}. Run `ltp sync` first to generate the dashboard model."
        )
    if static is None:
        static = Path(__file__).resolve().parents[1] / "dashboard" / "dist"
    static = static.expanduser().resolve(strict=True)
    if not static.is_dir() or not (static / "index.html").is_file():
        raise FileNotFoundError(f"Dashboard build is missing or incomplete: {static}")
    return DashboardPaths(project=project, dashboard=dashboard, static=static)


def _file_meta(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"exists": False, "name": path.name}
    stat = path.stat()
    return {
        "exists": True,
        "name": path.name,
        "modified_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def _safe_static_file(static_root: Path, request_path: str) -> Optional[Path]:
    decoded = unquote(request_path)
    if not decoded.startswith("/assets/"):
        return None
    relative = decoded.removeprefix("/assets/")
    parts = PurePosixPath(relative).parts
    if not relative or any(part in {"", ".", ".."} for part in parts):
        return None
    candidate = (static_root / "assets" / Path(*parts)).resolve()
    assets_root = (static_root / "assets").resolve()
    try:
        candidate.relative_to(assets_root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def make_handler(paths: DashboardPaths, quiet: bool = False):
    class DashboardHandler(BaseHTTPRequestHandler):
        server_version = "LTP/0.1"

        def log_message(self, format_string: str, *args: object) -> None:
            if not quiet:
                super().log_message(format_string, *args)

        def _headers(self, status: int, content_type: str, length: int = 0) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)
            self.end_headers()

        def _bytes(self, status: int, content_type: str, body: bytes, head: bool) -> None:
            self._headers(status, content_type, len(body))
            if not head:
                self.wfile.write(body)

        def _file(self, path: Path, head: bool) -> None:
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            body = path.read_bytes()
            self._bytes(HTTPStatus.OK, content_type, body, head)

        def _route(self, head: bool = False) -> None:
            path = urlsplit(self.path).path
            if path in {"/", "/index.html"}:
                self._file(paths.static / "index.html", head)
                return
            if path == "/api/dashboard":
                self._file(paths.dashboard, head)
                return
            if path == "/api/meta":
                body = json.dumps(
                    {"model": _file_meta(paths.dashboard)},
                    separators=(",", ":"),
                ).encode("utf-8")
                self._bytes(HTTPStatus.OK, "application/json; charset=utf-8", body, head)
                return
            asset = _safe_static_file(paths.static, path)
            if asset:
                self._file(asset, head)
                return
            body = b"Not found\n"
            self._bytes(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", body, head)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            self._route()

        def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            self._route(head=True)

        def do_POST(self) -> None:  # noqa: N802 - explicit read-only response
            self._bytes(
                HTTPStatus.METHOD_NOT_ALLOWED,
                "text/plain; charset=utf-8",
                b"Dashboard is read only\n",
                False,
            )

    return DashboardHandler


def create_server(
    project: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    allow_network: bool = False,
    static: Optional[Path] = None,
    quiet: bool = False,
) -> ThreadingHTTPServer:
    validate_bind_host(host, allow_network)
    paths = resolve_paths(project, static)
    server = ThreadingHTTPServer((host, port), make_handler(paths, quiet=quiet))
    server.daemon_threads = True
    return server


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve an ltp/ltp-model.yaml in a local, read-only dashboard."
    )
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Analyzed project root")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind address (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open a browser tab")
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Permit a non-loopback bind address such as 0.0.0.0",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress request logs")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        server = create_server(
            args.project,
            args.host,
            args.port,
            allow_network=args.allow_network,
            quiet=args.quiet,
        )
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    address, port = server.server_address[:2]
    url_host = "127.0.0.1" if address in {"0.0.0.0", "::"} else address
    url = f"http://{url_host}:{port}"
    print(f"ltp dashboard: {url}")
    print("Read only. Press Ctrl+C to stop.")
    if args.open_browser:
        threading.Timer(0.2, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
