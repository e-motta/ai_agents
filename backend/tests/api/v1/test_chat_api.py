import pytest
pytest.importorskip("fastapi")
pytest.importorskip("langchain")
pytest.importorskip("langchain_openai")
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.chat import router as chat_router
from app.dependencies import get_router_llm, get_math_llm, initialize_knowledge


class DummyLLM:
    def __init__(self, content):
        self._content = content

    async def ainvoke(self, messages):
        return SimpleNamespace(content=self._content)


class FailingLLM:
    async def ainvoke(self, messages):
        raise RuntimeError("router failed")


@pytest.fixture()
def client_factory():
    # Build a minimal FastAPI app to avoid startup warmups from app.main
    def _make(router_llm, math_llm):
        app = FastAPI()
        app.include_router(chat_router, prefix="/api/v1")
        app.dependency_overrides[get_router_llm] = lambda: router_llm
        app.dependency_overrides[get_math_llm] = lambda: math_llm
        app.dependency_overrides[initialize_knowledge] = lambda: True
        client = TestClient(app)
        return client

    return _make


def test_chat_math_flow_success(client_factory):
    client = client_factory(DummyLLM("MathAgent"), DummyLLM("5"))

    payload = {"message": "2 + 3", "user_id": "u1", "conversation_id": "c1"}
    resp = client.post("/api/v1/chat", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["router_decision"] == "MathAgent"
    assert data["response"] == "5"
    assert data["agent_workflow"][0]["agent"] == "RouterAgent"
    assert data["agent_workflow"][1]["agent"] == "MathAgent"


def test_chat_empty_message_returns_422(client_factory):
    client = client_factory(DummyLLM("MathAgent"), DummyLLM("5"))

    payload = {"message": "   ", "user_id": "u1", "conversation_id": "c1"}
    resp = client.post("/api/v1/chat", json=payload)

    assert resp.status_code == 422


def test_chat_error_flow_on_router_failure(client_factory):
    client = client_factory(FailingLLM(), DummyLLM("5"))

    payload = {"message": "hello", "user_id": "u1", "conversation_id": "c1"}
    resp = client.post("/api/v1/chat", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["router_decision"] == "Error"
    assert data["response"] == "Sorry, I could not process your request."
    assert data["agent_workflow"][1]["agent"] == "System"


def test_chat_unsupported_language_flow(client_factory):
    client = client_factory(DummyLLM("UnsupportedLanguage"), DummyLLM("0"))

    payload = {"message": "bonjour", "user_id": "u1", "conversation_id": "c1"}
    resp = client.post("/api/v1/chat", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["router_decision"] == "UnsupportedLanguage"
    assert data["response"].startswith("Unsupported language")
    assert data["agent_workflow"][1]["agent"] == "System"
