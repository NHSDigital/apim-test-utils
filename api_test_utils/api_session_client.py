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
        if not isinstance(url, str) :
            return url

        parsed = urlparse(url)
        if parsed.scheme:
            return url

        url = os.path.join(self.base_uri, url)
        return url

    def _retry_429s(self, make_request):
        fib_times = [0,1,1,2,3,5,8,13,21]
        fib_index = 0
        while True:
            get_resp = make_request()
            if get_resp.status == 429:
                time.sleep(fib_times[fib_index])
                fib_index += 1
                if fib_index == len(fib_times)-1:
                    return "Time out Error" # Replace with error exeption
                continue
            return get_resp

    def get(self, url: StrOrURL, *, allow_retries: bool = False, allow_redirects: bool = True, **kwargs: Any) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        if allow_retries:
            return self._retry_429s(lambda: self.session.get(uri, allow_redirects=allow_redirects, **kwargs))
        else:
            print(self.session.get(uri, allow_redirects=allow_redirects, **kwargs))
            return self.session.get(uri, allow_redirects=allow_redirects, **kwargs)
        

    def post(self, url: StrOrURL, *, allow_redirects: bool = True, **kwargs: Any) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        return self.session.post(uri, allow_redirects=allow_redirects, **kwargs)

    def put(self, url: StrOrURL, *, allow_redirects: bool = True, **kwargs: Any) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        return self.session.put(uri, allow_redirects=allow_redirects, **kwargs)

    def delete(self, url: StrOrURL, *, allow_redirects: bool = True, **kwargs: Any) -> "aoihttp._RequestContextManager":
        uri = self._full_url(url)
        return self.session.delete(uri, allow_redirects=allow_redirects, **kwargs)

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
