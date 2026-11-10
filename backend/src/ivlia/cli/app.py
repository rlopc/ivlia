"""`ivlia`: the command line. It uses ivlia only through the API."""

import logging
import webbrowser
from collections.abc import Callable
from typing import Annotated, NoReturn, assert_never

import typer
from pydantic import ValidationError

from ivlia.cli.client import ApiClient, ApiError
from ivlia.config.errors import ConfigError, StartupError
from ivlia.config.installation import resolve_installation
from ivlia.config.secrets import API_TOKEN, secret_store
from ivlia.config.settings import load_config
from ivlia.contract.events import EndEvent, ErrorEvent, TokenEvent
from ivlia.contract.requests import ChatRequest

type Connect = Callable[[], ApiClient]
type OpenBrowser = Callable[[str], bool]


def build_app(connect: Connect, open_browser: OpenBrowser) -> typer.Typer:
    """The CLI, with its ways out (API and browser) passed in for tests."""
    # Never show frame locals in a traceback: they can hold the token
    # (docs/standards/security.md).
    app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)

    @app.command()
    def ask(message: Annotated[str, typer.Argument(help="What to ask.")]) -> None:
        """Ask ivlia and print the answer as it arrives."""
        try:
            request = ChatRequest(message=message)
        except ValidationError as error:
            raise typer.BadParameter(
                error.errors()[0]["msg"], param_hint="MESSAGE"
            ) from None
        printed = False
        try:
            with connect() as client:
                for event in client.chat(request):
                    match event:
                        case TokenEvent(text=text):
                            typer.echo(text, nl=False)
                            printed = True
                        case ErrorEvent(message=error_message):
                            _fail(error_message, after_output=printed)
                        case EndEvent():
                            typer.echo()
                            return
                        case _:
                            # mypy fails here if an event type is not handled.
                            assert_never(event)
        except (ApiError, StartupError) as error:
            _fail(str(error), after_output=printed)
        _fail("The answer ended before it was complete.", after_output=printed)

    @app.command()
    def web() -> None:
        """Open the web in the browser, already signed in."""
        try:
            with connect() as client:
                link = client.session_link()
        except (ApiError, StartupError) as error:
            _fail(str(error))
        if not open_browser(link.url):
            typer.echo(
                f"Cannot open the browser. Open this link within 60 seconds:\n{link.url}"
            )

    return app


def _fail(message: str, *, after_output: bool = False) -> NoReturn:
    if after_output:
        typer.echo()  # End the half-printed answer's line.
    typer.echo(f"ivlia: {message}", err=True)
    raise typer.Exit(code=1)


def connect_from_config() -> ApiClient:
    """A client of this installation's API, with its port and token."""
    config = load_config(resolve_installation())
    store = secret_store(config.installation, config.settings.keyring_service)
    token = store.get(API_TOKEN)
    if token is None:
        msg = "There is no API token yet. Start the server once: `ivlia-server`."
        raise ConfigError(msg)
    return ApiClient.connect(config.port, token)


class _MessageOnly(logging.Formatter):
    """One line per record: tracebacks are for the server log, not the terminal."""

    def formatException(self, ei: object) -> str:  # noqa: ARG002, N802 (logging API)
        return ""


def _log_to_stderr() -> None:
    # The CLI has no log file: the JSON log is an adapter, which it may not import.
    handler = logging.StreamHandler()
    handler.setFormatter(_MessageOnly("ivlia: %(message)s"))
    logging.basicConfig(level=logging.WARNING, handlers=[handler])


def main() -> None:
    _log_to_stderr()
    build_app(connect_from_config, webbrowser.open)()
