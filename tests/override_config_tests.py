import json

import pytest

from api_test_utils.api_session_client import APISessionClient
from api_test_utils.api_test_session_config import APITestSessionConfig


@pytest.fixture
def api_test_config() -> APITestSessionConfig:

    yield APITestSessionConfig(base_uri="https://httpbin.org")


@pytest.mark.asyncio
async def test_fixture_override_http_bin_post(api_client: APISessionClient):
    data = {'test': 'data'}
    async with api_client.post("post", json=data) as resp:

        assert resp.status == 200

        body = await resp.json()

        assert body['headers'].get('Host') == 'httpbin.org'
        assert body['headers'].get('Content-Type') == 'application/json'
        assert body['data'] == json.dumps(data)
