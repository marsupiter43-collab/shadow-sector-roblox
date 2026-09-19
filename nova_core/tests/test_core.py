import pytest
import pytest_asyncio
from nova_core.engine.state_manager import StateManager
from nova_core.llm.parser import parse_llm_response
from nova_core.llm.client import LLMClient

def test_state_manager_defaults():
    sm = StateManager()
    assert sm.mood == "calm"
    assert sm.energy_level == 100
    assert sm.idle_seconds == 0

def test_state_manager_update_energy():
    sm = StateManager()
    sm.update_energy(-20)
    assert sm.energy_level == 80
    sm.update_energy(50)
    assert sm.energy_level == 100 # constrained
    sm.update_energy(-150)
    assert sm.energy_level == 0 # constrained

def test_state_manager_change_mood():
    sm = StateManager()
    sm.change_mood("curious")
    assert sm.mood == "curious"
    sm.change_mood("invalid_mood")
    assert sm.mood == "curious" # Should not change if invalid

def test_parse_llm_response_normal():
    raw = "<thought>Thinking about it.</thought>Hello!"
    thought, visible = parse_llm_response(raw)
    assert thought == "Thinking about it."
    assert visible == "Hello!"

def test_parse_llm_response_multiple_thoughts():
    raw = "<thought>Thought 1</thought>Some text<thought>Thought 2</thought>More text"
    thought, visible = parse_llm_response(raw)
    assert thought == "Thought 1\nThought 2"
    assert visible == "Some textMore text"

def test_parse_llm_response_no_thought():
    raw = "Just text"
    thought, visible = parse_llm_response(raw)
    assert thought == ""
    assert visible == "Just text"

@pytest.mark.asyncio
async def test_llm_client_mock():
    # Since we shouldn't actually call Ollama in a unit test, we mock httpx
    client = LLMClient()

    # Simple monkeypatching for test
    async def mock_post(*args, **kwargs):
        class MockResponse:
            def raise_for_status(self): pass
            def json(self): return {"response": "<thought>Mock thought</thought>Mock response"}
        return MockResponse()

    client.client.post = mock_post

    response = await client.generate_response("System", "Prompt")
    await client.close()

    assert response == "<thought>Mock thought</thought>Mock response"
