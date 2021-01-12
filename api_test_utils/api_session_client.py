import os
from types import TracebackType
from typing import Optional, Type, Any
from urllib.parse import urlparse
import time

import aiohttp
from aiohttp.typedefs import StrOrURL


class APISessionClient:
    """ wrapper to configuration of a base url for aiohttp session client """

    def __init__(self, base_uri, **kwargs):
        self.base_uri = base_uri
        self.session = aiohttp.ClientSession(**kwargs)

    async def __aenter__(self) -> "APISessionClient":
        return self

    def _full_url(self, url: StrOrURL) -> StrOrURL:
        if not isinstance(url, str):
            return url

        parsed = urlparse(url)
        if parsed.scheme:
            return url

        url = os.path.join(self.base_uri, url)
        return url

    async def _retry_requests(self, make_request, max_retries):
        retry_codes = {429, 503}
        for retry_number in range(max_retries):
            resp = await make_request()
            if resp.status in retry_codes:
                time.sleep(2**retry_number - 1)
                continue
            return resp
        else:
            raise TimeoutError("Time out on request retries")

    def get(
        self,
        url: StrOrURL,
        *,
        allow_retries: bool = False,
        max_retries: int = 5,
        allow_redirects: bool = True,
        **kwargs: Any
    ) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        if allow_retries:
            resp = self._retry_requests(
                lambda: self.session.get(
                    uri, allow_redirects=allow_redirects, **kwargs
                ),
                max_retries=max_retries
            )
        else:
            resp = self.session.get(
                uri, allow_redirects=allow_redirects, **kwargs
            )
        return resp

    def post(
        self,
        url: StrOrURL,
        *,
        allow_retries: bool = False,
        max_retries: int = 5,
        allow_redirects: bool = True,
        **kwargs: Any
    ) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        if allow_retries:
            resp = self._retry_requests(
                lambda: self.session.post(
                    uri, allow_redirects=allow_redirects, **kwargs
                ),
                max_retries=max_retries
            )
        else:
            resp = self.session.post(
                uri, allow_redirects=allow_redirects, **kwargs
            )
        return resp

    def put(
        self,
        url: StrOrURL,
        *,
        allow_retries: bool = False,
        max_retries: int = 5,
        allow_redirects: bool = True,
        **kwargs: Any
    ) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        if allow_retries:
            resp = self._retry_requests(
                lambda: self.session.put(
                    uri, allow_redirects=allow_redirects, **kwargs
                ),
                max_retries=max_retries
            )
        else:
            resp = self.session.put(
                uri, allow_redirects=allow_redirects, **kwargs
            )
        return resp

    def delete(
        self,
        url: StrOrURL,
        *,
        allow_retries: bool = False,
        max_retries: int = 5,
        allow_redirects: bool = True,
        **kwargs: Any
    ) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        if allow_retries:
            resp = self._retry_requests(
                lambda: self.session.delete(
                    uri, allow_redirects=allow_redirects, **kwargs
                ),
                max_retries=max_retries
            )
        else:
            resp = self.session.delete(
                uri, allow_redirects=allow_redirects, **kwargs
            )
        return resp

    async def close(self):
        await self.session.close()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()
