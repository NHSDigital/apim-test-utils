from api_test_utils.apigee_api import ApigeeApi
from api_test_utils.api_session_client import APISessionClient
from . import throw_friendly_error
from types import TracebackType
from typing import Optional, Type


class ApigeeApiProxies(ApigeeApi):
    """ Create dummy Apigee proxies for testing purposes """

    def __init__(self, org_name: str = "nhsd-nonprod"):
        super().__init__(org_name)

    async def __aenter__(self):
        await self._create_proxy()
        return self

    async def _create_proxy(self):
        async with APISessionClient(self.base_uri) as session:
            async with session.post(f"apis", headers=self.headers, json={'name': self.name}) as resp:
                body = await resp.json()
                if resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get details for proxy: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                return body

    async def _destroy_proxy(self):
        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"apis/{self.name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to delete proxy: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                return body

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self._destroy_proxy()
