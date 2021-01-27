from typing import Callable, Any, Awaitable, List, Tuple
from json import JSONDecodeError

import asyncio
from aiohttp import ClientResponse, ContentTypeError

from multidict import CIMultiDictProxy

__version__ = "0.0.0"


async def is_200(resp: ClientResponse):
    return resp.status == 200


async def is_404(resp: ClientResponse):
    return resp.status == 404


async def get_text_body(resp: ClientResponse) -> str:
    return await resp.text()


async def get_json_body(resp: ClientResponse):
    return await resp.json()


async def get_bytes_body(resp: ClientResponse) -> bytes:
    return await resp.read()


async def auto_load_body(resp: ClientResponse):
    content_type = resp.content_type.lower()
    if 'json' in content_type:
        try:
            return await get_json_body(resp)
        except (ContentTypeError, JSONDecodeError):
            return await get_text_body(resp)

    if 'text' in content_type or 'xml' in content_type:
        return await get_text_body(resp)

    return await get_bytes_body(resp)


class PollTimeoutError(TimeoutError):

    def __init__(self, responses: List[Tuple[int, CIMultiDictProxy, Any]]):
        self.responses = responses

        message = 'no responses received'

        if responses:

            status, headers, text = responses[-1]
            message = f"last status: {status}\nlast headers:{headers}\nlast body:{text}"

        super().__init__(message)


async def poll_until(
    make_request: Callable[[], Awaitable[ClientResponse]],
    until: Callable[[ClientResponse], Awaitable[bool]] = is_200,
    body_resolver: Callable[[ClientResponse], Awaitable[Any]] = auto_load_body,
    timeout: int = 5,
    sleep_for: float = 1
):
    """
        repeat an api request until a specified condition is met or raise a timeout
    Args:
        make_request: request factory, e.g. lambda: session.get('http://test.com')
        until: predicate to evaluate the response ,  e.g. lambda r: r.status == 404
        body_resolver: factory to resolve the body (evaluated on every response for tracking responses)
                        e.g.  lambda r: await r.body()
                        set to None not to retrieve the body, obviously retrieving the body will potentially have an
                        overhead, and attempt to parse or load invalid responses will break the polling

        timeout: timeout in seconds
        sleep_for: poll frequency in seconds

    Returns:
        List[Tuple[int, IMultiDictProxy, Any]]: responses received, (status, headers, body)
    """

    responses = []

    async def _poll_until():

        while True:

            async with make_request() as response:

                body = None

                if body_resolver is not None:
                    body = await body_resolver(response)

                responses.append((response.status, response.headers, body))
                should_stop = await until(response)
                if not should_stop:
                    await asyncio.sleep(sleep_for)
                    continue

                return responses

    try:
        return await asyncio.wait_for(_poll_until(), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise PollTimeoutError(responses) from e


def throw_friendly_error(message: str, url: str, status_code: int, response: str, headers: dict) -> Exception:
    raise Exception(f"\n{'*' * len(message)}\n"
                    f"MESSAGE: {message}\n"
                    f"URL: {url}\n"
                    f"STATUS CODE: {status_code}\n"
                    f"RESPONSE: {response}\n"
                    f"HEADERS: {headers}\n"
                    f"{'*' * len(message)}\n")
