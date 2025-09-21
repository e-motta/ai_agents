from langchain_openai.chat_models.base import ChatOpenAI
import pytest

pytest.importorskip("langchain")
pytest.importorskip("langchain_openai")
from types import SimpleNamespace

from app.agents.math_agent import solve_math


class DummyLLM(ChatOpenAI):
    def __init__(self, content):
        self._content = content

    async def ainvoke(self, messages):
        return SimpleNamespace(content=self._content)


@pytest.mark.asyncio
async def test_solve_math_simple_addition():
    llm = DummyLLM("5")
    result = await solve_math("2 + 3", llm)
    assert result == "5"


@pytest.mark.asyncio
async def test_solve_math_rejects_non_numeric_output():
    llm = DummyLLM("not-a-number")
    with pytest.raises(ValueError):
        await solve_math("how is the weather?", llm)


@pytest.mark.asyncio
async def test_solve_math_bubbles_error_as_value_error():
    class FailingLLM(ChatOpenAI):
        async def ainvoke(self, messages):
            raise RuntimeError("network error")

    with pytest.raises(ValueError) as exc:
        await solve_math("10/2", FailingLLM())
    assert "Error evaluating mathematical expression" in str(exc.value)
