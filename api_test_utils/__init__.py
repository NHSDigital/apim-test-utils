from typing import Callable, Any, Awaitable, List, Tuple
import asyncio
from aiohttp import ClientResponse, ContentTypeError
from json import JSONDecodeError

from multidict import CIMultiDictProxy


async def is_200(r: ClientResponse):
    return r.status == 200


async def is_404(r: ClientResponse):
    return r.status == 404


async def get_text_body(r: ClientResponse) -> str:
    return await r.text()


async def get_json_body(r: ClientResponse):
    return await r.json()


async def get_bytes_body(r: ClientResponse) -> bytes:
    return await r.read()


async def auto_load_body(r: ClientResponse):
    #ContentTypeError
    content_type = r.content_type.lower()
    if 'json' in content_type:
        try:
            return await get_json_body(r)
        except (ContentTypeError, JSONDecodeError):
            return await get_text_body(r)

    if 'text' in content_type or 'xml' in content_type:
        return await get_text_body(r)

    return await get_bytes_body(r)


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

            async with make_request() as r:

                body = None

                if body_resolver is not None:
                    body = await body_resolver(r)

                responses.append((r.status, r.headers, body))
                should_stop = await until(r)
                if not should_stop:
                    await asyncio.sleep(sleep_for)
                    continue

                return responses

    try:
        return await asyncio.wait_for(_poll_until(), timeout=timeout)
    except asyncio.TimeoutError as e:
        raise PollTimeoutError(responses) from e
