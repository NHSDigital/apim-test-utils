import pytest

from api_test_utils.api_test_session_config import APITestSessionConfig
from api_test_utils import poll_until, PollTimeoutError

from api_test_utils.api_session_client import APISessionClient


@pytest.fixture
def api_test_config() -> APITestSessionConfig:

    yield APITestSessionConfig(base_uri="https://httpbin.org")


@pytest.mark.asyncio
async def test_wait_for_poll_does_timeout(api_client: APISessionClient):

    with pytest.raises(PollTimeoutError) as xi:
        await poll_until(lambda: api_client.get('status/404'), timeout=1, sleep_for=0.3)

    x = xi.value  # type: PollTimeoutError
    assert len(x.responses) > 0
    assert x.responses[0][0] == 404


@pytest.mark.asyncio
async def test_wait_for_200_bytes(api_client: APISessionClient):

    responses = await poll_until(lambda: api_client.get('bytes/100'), timeout=5)

    assert len(responses) == 1

    status, headers, body = responses[0]

    assert status == 200
    assert headers.get('Content-Type').split(';')[0] == 'application/octet-stream'
    assert type(body) == bytes


@pytest.mark.asyncio
async def test_wait_for_200_json(api_client: APISessionClient):

    responses = await poll_until(lambda: api_client.get('json'), timeout=5)

    assert len(responses) == 1

    status, headers, body = responses[0]

    assert status == 200
    assert headers.get('Content-Type').split(';')[0] == 'application/json'
    assert body['slideshow']['title'] == 'Sample Slide Show'


@pytest.mark.asyncio
async def test_wait_for_200_html(api_client: APISessionClient):

    responses = await poll_until(lambda: api_client.get('html'), timeout=5)

    assert len(responses) == 1

    status, headers, body = responses[0]

    assert status == 200
    assert headers.get('Content-Type').split(';')[0] == 'text/html'
    assert type(body) == str
    assert body.startswith('<!DOCTYPE html>')


@pytest.mark.asyncio
async def test_wait_for_200_json_gzip(api_client: APISessionClient):

    responses = await poll_until(lambda: api_client.get('gzip'), timeout=5)

    assert len(responses) == 1

    status, headers, body = responses[0]

    assert status == 200
    assert headers.get('Content-Type').split(';')[0] == 'application/json'
    assert body['gzipped'] is True


@pytest.mark.asyncio
async def test_wait_for_200_json_deflate(api_client: APISessionClient):

    responses = await poll_until(lambda: api_client.get('deflate'), timeout=5)

    assert len(responses) == 1

    status, headers, body = responses[0]

    assert status == 200
    assert headers.get('Content-Type').split(';')[0] == 'application/json'
    assert body['deflated'] is True


# @pytest.mark.skip('we probably do not need brotli support just yet, but if we do .. add brotlipy')
@pytest.mark.asyncio
async def test_wait_for_200_json_brotli(api_client: APISessionClient):

    responses = await poll_until(lambda: api_client.get('brotli'), timeout=5)

    assert len(responses) == 1

    status, headers, body = responses[0]

    assert status == 200
    assert headers.get('Content-Type').split(';')[0] == 'application/json'
    assert body['brotli'] is True
