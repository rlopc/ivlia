"""Export of the event contract and the OpenAPI document.

Both are generated from the code and versioned, so that clients and reviewers
see every contract change. Run it with `just contract`.
"""

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import SecretStr, TypeAdapter

from ivlia.api.app import create_app
from ivlia.config.installation import Environment, Installation
from ivlia.config.settings import Config, Settings
from ivlia.contract.events import Event

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ivlia.domain.agents.state import AgentState

EVENTS_FILE = "events.schema.json"
OPENAPI_FILE = "openapi.json"


def events_schema() -> dict[str, Any]:
    schema = TypeAdapter(Event).json_schema(mode="serialization")
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}


def openapi_document() -> dict[str, Any]:
    """The document of the use installation, built without real settings or secrets."""

    async def no_chat(_state: AgentState) -> AsyncIterator[Event]:
        raise NotImplementedError
        yield

    config = Config(
        installation=Installation(env=Environment.USE, home=Path("/nonexistent")),
        settings=Settings.model_construct(),
    )
    return create_app(config, SecretStr("unused"), no_chat).openapi()


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def exports() -> dict[str, str]:
    """The text of each exported file, by file name."""
    return {
        EVENTS_FILE: render(events_schema()),
        OPENAPI_FILE: render(openapi_document()),
    }


def main() -> None:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(exist_ok=True)
    for name, text in exports().items():
        (out_dir / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
