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
async def test_200_with_allow_retries():
    async with APISessionClient("https://httpbin.org") as session:
        async with await session.get("get", allow_retries=True) as resp:
            assert resp.status == 200


@pytest.mark.asyncio
async def test_429_without_allow_retries():
    async with APISessionClient("https://httpbin.org") as session:
        async with await session.get("status/429", allow_retries=False) as resp:
            assert resp.status == 429


@pytest.mark.asyncio
async def test_503_without_allow_retries():
    async with APISessionClient("https://httpbin.org") as session:
        async with await session.get("status/503", allow_retries=False) as resp:
            assert resp.status == 503


@pytest.mark.slow
@pytest.mark.asyncio
async def test_429_with_allow_retries():
    async with APISessionClient("https://httpbin.org") as session:
        with pytest.raises(TimeoutError) as excinfo:
            await session.get("status/429", allow_retries=True, max_retries=3)

        error = excinfo.value
        assert "Time out on request retries" in str(error)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_503_with_allow_retries():
    async with APISessionClient("https://httpbin.org") as session:
        with pytest.raises(TimeoutError) as excinfo:
            await session.get("status/503", allow_retries=True, max_retries=3)

        error = excinfo.value
        assert "Time out on request retries" in str(error)

# Test other methods
# How to simulate behaviour of different responses coming back? - override the request function to send the requests back (Only if have extra time as behaviour covered)

# Parametrizing tests
# Try exponential back off rather than fib
# Python generators - how to generate next n in sequence
# Do that with number of retries
