import pytest

from api_test_utils.api_session_client import APISessionClient
from api_test_utils.api_test_session_config import APITestSessionConfig


@pytest.fixture(scope='function')
async def api_client(api_test_config: APITestSessionConfig):

    session_client = APISessionClient(api_test_config.base_uri)

    yield session_client

    await session_client.close()



