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
    ("status/503", False, 503),
    ("status/409", False, 409)
])
async def test_get_status_code_retries(endpoint, should_retry, expected):
    async with APISessionClient("https://httpbin.org") as session:
        async with session.get(endpoint, allow_retries=should_retry) as resp:
            assert resp.status == expected


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint, should_retry, expected_error", [
    ("status/429", True, "Maximum retry limit hit."),
    ("status/503", True, "Maximum retry limit hit."),
    ("status/409", True, "Maximum retry limit hit.")
])
async def test_max_retries_limit(endpoint, should_retry, expected_error):
    async with APISessionClient("https://httpbin.org") as session:
        with pytest.raises(TimeoutError) as excinfo:
            await session.get(endpoint, allow_retries=should_retry, max_retries=3)

        error = excinfo.value
        assert expected_error in str(error)


class MockRequest:
    """Class for returning multiple different function calls"""
    def __init__(self, iterable):
        self.iterator = iter(iterable)

    async def __call__(self):
        return next(self.iterator)


class MockStatus:
    """Mocks a Response status"""
    def __init__(self, status):
        self.status = status


def mock_response(code):
    return MockStatus(code)


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.parametrize("status_codes, max_retries, expected_response", [
    ([429, 429, 200, 200], 4, 200),
    ([503, 429, 409, 200], 4, 200),
])
async def test_retry_request_varying_responses(status_codes, max_retries, expected_response):
    async with APISessionClient("https://httpbin.org") as session:
        mock_status_list = map(mock_response, status_codes)
        requester = MockRequest(mock_status_list)
        resp = await session._retry_requests(requester, max_retries) # pylint: disable=W0212
        assert resp.status == expected_response


@pytest.mark.slow
@pytest.mark.asyncio
async def test_retry_request_varying_error():
    async with APISessionClient("https://httpbin.org") as session:
        mock_status_list = map(mock_response, [429, 429, 503])
        requester = MockRequest(mock_status_list)
        with pytest.raises(TimeoutError) as excinfo:
            await session._retry_requests(requester, max_retries=3) # pylint: disable=W0212
            error = excinfo.value
            assert error == "Maximum retry limit hit."
