import pytest


@pytest.fixture
def anyio_backend():
    """Run async tests on asyncio only to avoid optional trio dependency in CI."""
    return "asyncio"
