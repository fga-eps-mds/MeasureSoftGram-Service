import pytest

from utils.managers import CacheManager


@pytest.fixture(autouse=True)
def clear_cache_manager():
    CacheManager.last_call = {
        "function_name": None,
        "args": None,
        "kwargs": {},
        "return": None,
        "model_name": None,
    }
