"""`ivlia-server`: runs the API on 127.0.0.1, in development and in use."""

import argparse
import sys
from pathlib import Path

import uvicorn

from ivlia.bootstrap import build_server
from ivlia.config.errors import StartupError
from ivlia.config.installation import Environment, resolve_installation

HOST = "127.0.0.1"
"""Only this Mac: opening the API to the network would need real authentication."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ivlia-server", description=__doc__)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="restart on code changes (dev installation only)",
    )
    args = parser.parse_args(argv)
    try:
        # Checked before building anything, which would create the token.
        if args.reload and resolve_installation().env is not Environment.DEV:
            sys.stderr.write(
                "ivlia-server: --reload is only for the dev installation.\n"
            )
            return 2
        server = build_server()
    except StartupError as error:
        sys.stderr.write(f"ivlia-server: {error}\n")
        return 1
    config = server.config
    sys.stderr.write(
        f"ivlia-server: listening on http://{HOST}:{config.port} "
        f"(log: {server.log_file})\n"
    )
    # Reload mode needs an import string; it rebuilds the app in a subprocess.
    target = "ivlia.bootstrap:app_factory" if args.reload else server.app
    # log_config=None sends uvicorn's records to ivlia's JSON log. No access
    # log: request lines carry query strings, and so one-time link codes.
    uvicorn.run(
        target,
        host=HOST,
        port=config.port,
        log_config=None,
        access_log=False,
        factory=args.reload,
        reload=args.reload,
        reload_dirs=[str(Path(__file__).parent)] if args.reload else None,
    )
    return 0
