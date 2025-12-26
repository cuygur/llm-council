import pytest
from unittest.mock import patch, AsyncMock
from backend import council

@pytest.mark.asyncio
async def test_resolve_council_mode_standard():
    personas = await council.resolve_council_mode("standard", "query", ["m1"], "chairman")
    assert personas == {}

@pytest.mark.asyncio
async def test_resolve_council_mode_specialist():
    mock_response = {
        "content": '```json\n{"m1": "expert role"}\n```'
    }
    
    with patch("backend.council.query_model", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_response
        
        personas = await council.resolve_council_mode("specialist", "query", ["m1"], "chairman")
        
        assert personas == {"m1": "expert role"}
        assert mock_query.called

@pytest.mark.asyncio
async def test_get_council_config(test_data_dir):
    conversation = {
        "mode": "standard",
        "council_models": ["m1"],
        "chairman_model": "c1",
        "model_personas": {}
    }
    
    models, chairman, personas = await council.get_council_config(conversation, "query")
    assert models == ["m1"]
    assert chairman == "c1"
    assert personas == {}

