from typing import TYPE_CHECKING

import pytest
from port_contracts.llm import LLMContract

from ivlia.adapters.hello_world_llm import HelloWorldLLM

if TYPE_CHECKING:
    from ivlia.domain.models.llm import LLM


class TestHelloWorldLLM(LLMContract):
    @pytest.fixture
    def adapter(self) -> LLM:
        return HelloWorldLLM()
