import json

import pytest

from api_test_utils.api_session_client import APISessionClient


@pytest.mark.asyncio
async def test_postman_echo_read_multivalue_headers():
    async with APISessionClient("http://postman-echo.com") as session:
        async with session.get("response-headers?foo1=bar1&foo1=bar2") as resp:
            bars = resp.headers.getall('foo1')
            assert bars == ['bar1', 'bar2']


@pytest.mark.asyncio
async def test_postman_echo_send_multivalue_headers():
    async with APISessionClient("http://postman-echo.com") as session:
        async with session.get("headers", headers=[("foo1", "bar1"), ("foo1", "bar2")]) as resp:
            assert resp.status == 200
            body = await resp.json()

            assert body["headers"]["foo1"] == "bar1, bar2"


@pytest.mark.asyncio
async def test_fixture_postman_echo_send_multivalue_headers(api_client: APISessionClient):

    async with api_client.get("headers", headers=[("foo1", "bar1"), ("foo1", "bar2")]) as resp:
        assert resp.status == 200
        body = await resp.json()

        assert body["headers"]["foo1"] == "bar1, bar2"


@pytest.mark.asyncio
async def test_explicit_uri_http_bin_post(api_client: APISessionClient):

    data = {'test': 'data'}
    async with api_client.post("https://httpbin.org/post", json=data) as resp:

        assert resp.status == 200

        body = await resp.json()

        assert body['headers'].get('Host') == 'httpbin.org'
        assert body['headers'].get('Content-Type') == 'application/json'
        assert body['data'] == json.dumps(data)


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint, should_retry, expected", [
    ("get", True, 200),
    ("status/429", False, 429),
    ("status/503", False, 503)
])
async def test_status_code_retries(endpoint, should_retry, expected):
    async with APISessionClient("https://httpbin.org") as session:
        async with await session.get(endpoint, allow_retries=should_retry) as resp:
            assert resp.status == expected


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint, should_retry, expected_error", [
    ("status/429", True, "Maxium retry limit hit."),
    ("status/503", True, "Maxium retry limit hit.")
])
async def test_max_retries_limit(endpoint, should_retry, expected_error):
    async with APISessionClient("https://httpbin.org") as session:
        with pytest.raises(TimeoutError) as excinfo:
            await session.get(endpoint, allow_retries=should_retry, max_retries=3)

        error = excinfo.value
        assert expected_error in str(error)
