import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
import json

@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "LLM Council API"}

@pytest.mark.asyncio
async def test_config_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Get config
        response = await ac.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "council_models" in data
        assert "chairman_model" in data
        
        # Update config
        new_config = {
            "council_models": ["m1", "m2"],
            "chairman_model": "m3"
        }
        response = await ac.post("/api/config", json=new_config)
        assert response.status_code == 200
        assert response.json()["council_models"] == ["m1", "m2"]

@pytest.mark.asyncio
async def test_conversation_lifecycle(test_data_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create
        response = await ac.post("/api/conversations", json={"mode": "standard"})
        assert response.status_code == 200
        conv_id = response.json()["id"]
        
        # List
        response = await ac.get("/api/conversations")
        assert len(response.json()) == 1
        
        # Get
        response = await ac.get(f"/api/conversations/{conv_id}")
        assert response.status_code == 200
        assert response.json()["id"] == conv_id
        
        # Delete
        response = await ac.delete(f"/api/conversations/{conv_id}")
        assert response.status_code == 200
        
        # Get again (should be 404)
        response = await ac.get(f"/api/conversations/{conv_id}")
        assert response.status_code == 404
