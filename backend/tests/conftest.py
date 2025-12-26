import pytest
import os
import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def test_data_dir(tmp_path):
    """Create a temporary directory for test data and patch relevant modules."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    import backend.config
    import backend.storage
    
    original_config_dir = backend.config.DATA_DIR
    original_storage_dir = backend.storage.DATA_DIR
    
    backend.config.DATA_DIR = str(data_dir)
    backend.storage.DATA_DIR = str(data_dir)
    
    yield str(data_dir)
    
    backend.config.DATA_DIR = original_config_dir
    backend.storage.DATA_DIR = original_storage_dir
