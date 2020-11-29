import os
import pytest

from api_test_utils.fixtures import api_client  # pylint: disable=unused-import
from api_test_utils.api_test_session_config import APITestSessionConfig


@pytest.fixture(scope='function')
def api_test_config() -> APITestSessionConfig:
    os.environ.setdefault('APIGEE_ENVIRONMENT', 'prod')
    os.environ.setdefault('API_BASE_DOMAIN', 'postman-echo.com')

    return APITestSessionConfig()
