import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.council import check_clarification_needs
from backend.main import app
from httpx import AsyncClient, ASGITransport
import json

@pytest.mark.asyncio
async def test_check_clarification_needs_ambiguous():
    """Test that ambiguous queries return questions."""
    
    # Mock response from query_model
    mock_response = {
        "content": '["What is the goal?", "Which language?"]',
        "usage": {"prompt_tokens": 10, "completion_tokens": 10}
    }
    
    with patch("backend.council.query_model", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_response
        
        questions = await check_clarification_needs("Make a program")
        
        assert len(questions) == 2
        assert questions[0] == "What is the goal?"
        assert questions[1] == "Which language?"
        
        # Verify prompt contained request
        call_args = mock_query.call_args
        assert "Make a program" in call_args[0][1][0]["content"]

@pytest.mark.asyncio
async def test_check_clarification_needs_clear():
    """Test that clear queries return empty list."""
    
    mock_response = {
        "content": "CLEAR",
        "usage": {}
    }
    
    with patch("backend.council.query_model", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_response
        
        questions = await check_clarification_needs("Calculate 2+2 in Python")
        
        assert questions == []

@pytest.mark.asyncio
async def test_check_clarification_needs_json_block():
    """Test parsing when model returns markdown code block."""
    
    mock_response = {
        "content": '```json\n["Question 1", "Question 2"]\n```',
        "usage": {}
    }
    
    with patch("backend.council.query_model", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_response
        
        questions = await check_clarification_needs("Ambiguous")
        
        assert len(questions) == 2
        assert questions[0] == "Question 1"

@pytest.mark.asyncio
async def test_clarification_stream_integration(test_data_dir):
    """Test that stream emits clarification event."""
    
    # Mock storage to use test dir (via conftest fixture usually, but we patch storage functions)
    # Actually, if we use client with app, it uses real storage module.
    # The 'test_data_dir' fixture in conftest likely sets up a temp dir and patches config.DATA_DIR
    
    # We'll mock check_clarification_needs in main.py
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # Create conversation first
        response = await ac.post("/api/conversations", json={"mode": "standard"})
        conv_id = response.json()["id"]
        
        with patch("backend.main.check_clarification_needs", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = ["Q1", "Q2"]
            
            # Send message that triggers clarification
            # stream endpoint
            
            # We need to capture the SSE stream
            async with ac.stream("POST", f"/api/conversations/{conv_id}/message/stream", json={"content": "Vague request"}) as response:
                
                events = []
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))
                
                # Check events
                clarification_event = next((e for e in events if e["type"] == "clarification_needed"), None)
                assert clarification_event is not None
                assert clarification_event["data"]["questions"] == ["Q1", "Q2"]
                
                # Should verify it stopped execution (no stage1_start)
                assert not any(e["type"] == "stage1_start" for e in events)
                
                # Verify complete event
                assert events[-1]["type"] == "complete"

