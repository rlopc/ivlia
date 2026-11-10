"""Composition root: builds the application and wires adapters to ports.

It is the only module that imports adapters.
"""

from dataclasses import dataclass
from importlib.metadata import version
from typing import TYPE_CHECKING

from opentelemetry import trace

from ivlia.adapters.hello_world_llm import HelloWorldLLM
from ivlia.adapters.observability.logs import LOG_FILE, configure_logging
from ivlia.adapters.observability.traces import tracer_provider
from ivlia.adapters.sqlite.memory import open_memory_db
from ivlia.api.app import create_app
from ivlia.api.spa import built_spa
from ivlia.application.chat import Chat
from ivlia.application.orchestration.graph import build_graph
from ivlia.config.installation import resolve_installation
from ivlia.config.secrets import api_token, secret_store
from ivlia.config.settings import Config, load_config

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi import FastAPI


@dataclass(frozen=True, slots=True)
class Server:
    app: FastAPI
    config: Config
    log_file: Path


def build_server() -> Server:
    """Validate everything and build the app, in start order.

    Raises `StartupError`, whose message says what fails.
    """
    ivlia_version = version("ivlia")
    config = load_config(resolve_installation())
    home, settings = config.installation.home, config.settings
    # Created first and private: later mkdirs with parents=True would use the umask.
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    home.chmod(0o700)
    configure_logging(home, log_content=settings.log_content)
    trace.set_tracer_provider(
        tracer_provider(home, ivlia_version, console=settings.trace_console)
    )
    open_memory_db(home, ivlia_version).close()
    token = api_token(secret_store(config.installation, settings.keyring_service))
    chat = Chat(build_graph(HelloWorldLLM()))
    app = create_app(config, token, chat, spa_dir=built_spa())
    return Server(app=app, config=config, log_file=home / LOG_FILE)


def app_factory() -> FastAPI:
    """Entry point for uvicorn's reload mode, which needs an import string."""
    return build_server().app
