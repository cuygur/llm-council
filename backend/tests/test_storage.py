import os
import json
from backend import storage

def test_create_conversation(test_data_dir):
    conversation_id = "test-conv-1"
    storage.create_conversation(conversation_id, council_models=["model1"], chairman_model="model2")
    
    path = storage.get_conversation_path(conversation_id)
    assert os.path.exists(path)
    
    with open(path, 'r') as f:
        data = json.load(f)
        assert data["id"] == conversation_id
        assert data["council_models"] == ["model1"]
        assert data["chairman_model"] == "model2"

def test_get_conversation(test_data_dir):
    conversation_id = "test-conv-2"
    storage.create_conversation(conversation_id)
    
    conv = storage.get_conversation(conversation_id)
    assert conv is not None
    assert conv["id"] == conversation_id
    
    assert storage.get_conversation("non-existent") is None

def test_delete_conversation(test_data_dir):
    conversation_id = "test-conv-3"
    storage.create_conversation(conversation_id)
    
    assert storage.delete_conversation(conversation_id) is True
    assert storage.get_conversation(conversation_id) is None
    assert storage.delete_conversation(conversation_id) is False

def test_list_conversations(test_data_dir):
    storage.create_conversation("c1")
    storage.create_conversation("c2")
    
    convs = storage.list_conversations()
    assert len(convs) == 2
    ids = [c["id"] for c in convs]
    assert "c1" in ids
    assert "c2" in ids
