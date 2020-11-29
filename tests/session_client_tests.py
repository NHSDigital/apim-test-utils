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
