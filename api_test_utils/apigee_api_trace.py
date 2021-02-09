from uuid import uuid4
from . import get_token, throw_friendly_error
from api_test_utils.apigee_api import ApigeeApi
from api_test_utils.api_session_client import APISessionClient


class ApigeeApiTraceDebug(ApigeeApi):
    """ Create and collect Apigee Trace information for debugging purposes """

    def __init__(self, proxy: str, environment: str = "internal-dev", timeout: int = 10,
                 org_name: str = "nhsd-nonprod"):
        super().__init__(org_name)

        self.proxy = proxy
        self.env = environment
        self.default_params = {
            "session": self.name,
            "timeout": timeout,
        }

    @property
    def proxy(self):
        return self.proxy

    @proxy.setter
    def proxy(self, new_proxy):
        self.proxy = new_proxy

    async def _get_latest_revision(self, proxy: str = self.proxy) -> str:
        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"apis/{proxy}/revisions", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get revision for: {proxy} on {self.env}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def start_trace(self, proxy: str = self.proxy):
        revision = await self._get_latest_revision(proxy)

        async with APISessionClient(self.base_uri) as session:
            async with session.post(f"/environments/{self.env}/apis/{proxy}/revisions/{revision}/debugsessions",
                                    params=self.default_params,
                                    headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to start trace on proxy: {proxy}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def _get_transaction_id(self) -> str:
        async with APISessionClient(self.base_uri) as session:
            async with session.post(f"/environments/{self.env}/apis/{self.proxy}/revisions/{revision}/"
                                    f"debugsessions/{self.name}/data",
                                    params=self.default_params,
                                    headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get transaction_id for session: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                return body.strip('[]').replace("\"", "").strip().split(', ')[0]

    async def get_raw_trace_data(self) -> dict:
        transaction_id = await self._get_transaction_id()

        async with APISessionClient(self.base_uri) as session:
            async with session.post(f"/environments/{self.env}/apis/{self.proxy}/revisions/{revision}/"
                                    f"debugsessions/{self.name}/data/{transaction_id}",
                                    params=self.default_params,
                                    headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get trace data for session {self.name} on proxy {proxy}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def stop_trace(self):
        transaction_id = await self._get_transaction_id()

        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"/environments/{self.env}/apis/{self.proxy}/revisions/{revision}/"
                                      f"debugsessions/{self.name}/data/{transaction_id}",
                                      params=self.default_params,
                                      headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"failed to stop trace: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    def get_asid_from_trace(self) -> dict:
        data = self.get_raw_trace_data()
        executions = [x.get('results', None) for x in data['point'] if x.get('id', "") == "Execution"]
        executions = list(filter(lambda x: x != [], executions))

        request_messages = []
        variable_accesses = []
        asid = {}

        for execution in executions:
            for item in execution:
                if item.get('ActionResult', '') == 'RequestMessage':
                    request_messages.append(item)
                elif item.get('ActionResult', '') == 'VariableAccess':
                    variable_accesses.append(item)

        for result in request_messages:  # One being sent as the header
            for item in result['headers']:
                if item['name'] == 'NHSD-ASID':
                    asid['request_header'] = item['value']
                    break
            if len(asid) > 0:
                break

        for result in variable_accesses:  # Configured by the application
            for item in result['accessList']:
                if item.get('Get', {}).get('name', '') == 'app.asid':
                    asid['application_configured'] = item.get('Get', {}).get('value', None)
                    break
        return asid
