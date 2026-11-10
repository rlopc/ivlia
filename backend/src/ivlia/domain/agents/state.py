"""Agent state, independent of the orchestration framework."""

from dataclasses import dataclass
from typing import Literal

type Role = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class AgentState:
    messages: tuple[Message, ...] = ()
