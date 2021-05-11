from ast import literal_eval
from api_test_utils.apigee_api import ApigeeApi
from api_test_utils.api_session_client import APISessionClient
from . import throw_friendly_error


class ApigeeApiTraceDebug(ApigeeApi):
    """ Create and collect Apigee Trace information for debugging purposes """

    def __init__(self, proxy: str, environment: str = "internal-dev", timeout: int = 30,
                 org_name: str = "nhsd-nonprod"):
        super().__init__(org_name)

        self.proxy = proxy
        self.env = environment
        self.default_params = {
            "session": self.name,
            "timeout": str(timeout),
        }
        self.revision = None
        self.transaction_id = None

    async def _set_latest_revision(self):
        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"apis/{self.proxy}/revisions", headers=self.headers) as resp:
                body = await resp.read()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get revision for: {self.proxy} on {self.env}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                # Get and validate revision number
                revision = literal_eval(body.decode("UTF-8"))[-1]
                assert revision.isnumeric(), f"Revision must be a number: {revision}"

                self.revision = revision

    def _has_timed_out(self, resp):
        if resp.get("message", "") == f"DebugSession {self.name} not found":
            raise TimeoutError("Your session has timed out, please rerun the start_trace() method again")

    async def start_trace(self) -> dict:
        await self._set_latest_revision()
        async with APISessionClient(self.base_uri) as session:
            async with session.post(
                    f"environments/{self.env}/apis/{self.proxy}/revisions/{self.revision}/debugsessions",
                    params=self.default_params,
                    headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to start trace on proxy: {self.proxy}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return {'status_code': resp.status, 'body': body}

    async def _set_transaction_id(self):
        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"environments/{self.env}/apis/{self.proxy}/revisions/{self.revision}/"
                                   f"debugsessions/{self.name}/data",
                                   headers=self.headers) as resp:

                body = await resp.json()
                if resp.status != 200:
                    self._has_timed_out(body)
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get transaction_id for session: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                self.transaction_id = body[0].strip() if body else None

    async def get_trace_data(self) -> dict or None:
        if not self.revision:
            raise RuntimeError("You must run start_trace() before you can run get_raw_trace()")

        await self._set_transaction_id()
        if not self.transaction_id:
            return None

        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"environments/{self.env}/apis/{self.proxy}/revisions/{self.revision}/"
                                    f"debugsessions/{self.name}/data/{self.transaction_id}",
                                    headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get trace data for session {self.name} "
                                                 f"on proxy {self.proxy}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def stop_trace(self) -> dict:
        if not self.revision:
            raise RuntimeError("You must run start_trace() before you can run stop_trace()")

        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"environments/{self.env}/apis/{self.proxy}/revisions/{self.revision}/"
                                      f"debugsessions/{self.name}",
                                      headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"failed to stop trace: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                # Reset revision
                self.revision = None
                return {'status_code': resp.status, 'body': body}

    def get_asid_from_trace(self) -> dict:
        data = self.get_trace_data()
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

        for result in request_messages:  # ASID being sent in the header
            for item in result['headers']:
                if item['name'] == 'NHSD-ASID':
                    asid['request_header'] = item['value']
                    break
            if len(asid) > 0:
                break

        for result in variable_accesses:  # ASID configured by the application
            for item in result['accessList']:
                if item.get('Get', {}).get('name', '') == 'app.asid':
                    asid['application_configured'] = item.get('Get', {}).get('value', None)
                    break
        return asid

    def get_apigee_variable_from_trace(self, name: str) -> str or None:
        data = self.get_trace_data()
        executions = [x.get('results', None) for x in data['point'] if x.get('id', "") == "Execution"]
        executions = list(filter(lambda x: x != [], executions))

        variable_accesses = []

        for execution in executions:
            for item in execution:
                if item.get('ActionResult', '') == 'VariableAccess':
                    variable_accesses.append(item)

        for result in variable_accesses:  # Configured by the application
            for item in result['accessList']:
                if item.get('Get', {}).get('name', '') == name:
                    return item.get('Get', {}).get('value', '')

        return None

    def add_trace_filter(self, header_name: str, header_value: str):
        self.default_params[f"header_{header_name}"]=header_value
