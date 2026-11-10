"""Events streamed by the chat endpoint, as a union discriminated on `type`."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class _EventBase(BaseModel):
    # Fields with a default, like `type`, are always sent, so the exported
    # schema marks them as required.
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


class TokenEvent(_EventBase):
    type: Literal["token"] = "token"
    text: str


class EndEvent(_EventBase):
    type: Literal["end"] = "end"


class ErrorEvent(_EventBase):
    type: Literal["error"] = "error"
    message: str


Event = Annotated[TokenEvent | EndEvent | ErrorEvent, Field(discriminator="type")]
