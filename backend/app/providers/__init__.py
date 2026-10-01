from app.core.config import settings
from app.providers.base import BaseDataProvider
from app.providers.mock_provider import MockDataProvider
from app.providers.live_provider import LiveDataProvider


def get_data_provider() -> BaseDataProvider:
    if settings.USE_MOCK_DATA:
        return MockDataProvider()
    return LiveDataProvider()


__all__ = [
    "BaseDataProvider",
    "MockDataProvider",
    "LiveDataProvider",
    "get_data_provider",
]
