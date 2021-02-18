from os import environ
from uuid import uuid4
from time import time
from ast import literal_eval
import jwt  # pyjwt
from aiohttp.client_exceptions import ContentTypeError
from api_test_utils.api_session_client import APISessionClient
from . import throw_friendly_error
import asyncio


class OauthHelper:
    """ A helper class to interact with the different OAuth flows """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.proxy = self._get_proxy()
        self.base_uri = self._get_base_uri()

    @staticmethod
    def _get_proxy():
        _proxy = environ.get('OAUTH_PROXY', 'not-set').strip()
        if _proxy == 'not-set':
            raise RuntimeError('\nOAUTH_PROXY is missing from environment variables\n')
        return _proxy

    def _get_base_uri(self):
        _uri = environ.get('OAUTH_BASE_URI', 'not-set').strip()
        if _uri == 'not-set':
            raise RuntimeError('\nOAUTH_BASE_URI is missing from environment variables\n')
        return f"{_uri}/{self.proxy}"

    @staticmethod
    def _get_private_key():
        """Return the contents of a private key"""
        _path = environ.get("JWT_PRIVATE_KEY_ABSOLUTE_PATH", 'not-set').strip()
        if _path == 'not-set':
            raise RuntimeError("\nJWT_PRIVATE_KEY_ABSOLUTE_PATH is missing from environment variables\n")
        with open(_path, "r") as f:
            contents = f.read()
        if not contents:
            raise RuntimeError("Contents of file empty. Check JWT_PRIVATE_KEY_ABSOLUTE_PATH.")
        return contents

    async def get_authenticated_with_simulated_auth(self) -> str:
        """Get the code parameter value required to post to the oauth /token endpoint"""
        authenticator = _SimulatedAuthFlow(self.base_uri, self.client_id, self.redirect_uri)
        return await authenticator.authenticate()

    async def _get_default_authorization_code_request_data(self,
                                                           grant_type,
                                                           timeout: int = 5000,
                                                           refresh_token: str = None
                                                           ) -> dict:
        """Get the default data required for a authorization code request"""
        form_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': grant_type,
        }
        if refresh_token:
            form_data['refresh_token'] = refresh_token
            form_data['_refresh_token_expiry_ms'] = timeout
        else:
            form_data['redirect_uri'] = self.redirect_uri
            form_data['code'] = await self.get_authenticated_with_simulated_auth()
            form_data['_access_token_expiry_ms'] = timeout
        return form_data

    @staticmethod
    async def _get_default_client_credentials_request_data(grant_type: str, _jwt: bytes) -> dict:
        """Get the default data required for a client credentials request"""
        return {
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": _jwt,
            "grant_type": grant_type,
        }

    @staticmethod
    async def _retry_requests(make_request, max_retries):
        retry_codes = {429, 503, 409}
        for retry_number in range(max_retries):
            resp = await make_request()
            if resp.status in retry_codes:
                await asyncio.sleep(2 ** retry_number - 1)
                continue
            return resp
        raise TimeoutError("Maximum retry limit hit.")

    async def hit_oauth_endpoint(self, method: str, endpoint: str, **kwargs) -> dict:
        """Send a request to a OAuth endpoint"""
        async with APISessionClient(self.base_uri) as session:
            request_method = (session.post, session.get)[method.lower().strip() == 'get']
            resp = await self._retry_requests(lambda: request_method(endpoint, **kwargs), 5)
            try:
                body = await resp.json()
                _ = body.pop('message_id', None)  # Remove the unique message id if the response is na error
            except ContentTypeError:
                # Might be html or text response
                body = await resp.read()

                if isinstance(body, bytes):
                    # Convert into a string
                    body = str(body, "UTF-8")
                    try:
                        # In case json response was of type bytes
                        body = literal_eval(body)
                    except SyntaxError:
                        # Continue
                        pass

            return {'method': resp.method, 'url': resp.url, 'status_code': resp.status, 'body': body,
                    'headers': dict(resp.headers.items()), 'history': resp.history}

    async def get_token_response(self, grant_type: str, **kwargs) -> dict:
        if "data" not in kwargs:
            # Get defaults
            func = {
                'authorization_code': self._get_default_authorization_code_request_data,
                'refresh_token': self._get_default_authorization_code_request_data,
                'client_credentials': self._get_default_client_credentials_request_data,
            }.get(grant_type)

            kwargs['data'] = await func(grant_type, **kwargs)
        return await self.hit_oauth_endpoint("post", "token", data=kwargs['data'])

    def create_jwt(self,
                   kid: str,
                   signing_key: str = None,
                   claims: dict = None,
                   algorithm: str = "RS512",
                   client_id: str = None
                   ) -> bytes:
        """Create a Json Web Token"""
        if client_id is None:
            # Get default client id
            client_id = self.client_id
        if not signing_key:
            # Get default key
            signing_key = self._get_private_key()

        if not claims:
            # Get default claims
            claims = {
                "sub": client_id,
                "iss": client_id,
                "jti": str(uuid4()),
                "aud": f"{self.base_uri}/token",
                "exp": int(time()) + 5,
            }

        headers = ({}, {"kid": kid})[kid is not None]
        return jwt.encode(claims, signing_key, algorithm=algorithm, headers=headers)


class _SimulatedAuthFlow:
    def __init__(self, base_uri: str, client_id: str, redirect_uri: str):
        self.base_uri = base_uri
        self.client_id = client_id
        self.redirect_uri = redirect_uri

    async def _get_state(self, request_state: str) -> str:
        """Send an authorize request and retrieve the state"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": request_state
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.get("authorize", params=params) as resp:
                body = await resp.read()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message="unexpected response, unable to authenticate with simulated oauth",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                state = dict(resp.url.query)['state']

                # Confirm state is converted to a cryptographic value
                assert state != request_state
                return state

    async def authenticate(self, request_state: str = str(uuid4())) -> str:
        """Authenticate and retrieve the code value"""
        state = await self._get_state(request_state)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid",
            "state": state
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"state": state}

        async with APISessionClient(self.base_uri) as session:
            async with session.post("simulated_auth", params=params, data=payload, headers=headers,
                                    allow_redirects=False) as resp:
                if resp.status != 302:
                    body = await resp.json()
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message="unexpected response, unable to authenticate with simulated oauth",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                redirect_uri = resp.headers['Location'][resp.headers['Location'].index('callback'):]

                async with session.get(redirect_uri, allow_redirects=False) as callback_resp:
                    headers = dict(callback_resp.headers.items())
                    # Confirm request was successful
                    if callback_resp.status != 302:
                        body = await resp.read()
                        throw_friendly_error(message="unexpected response, unable to authenticate with simulated oauth",
                                             url=resp.url,
                                             status_code=resp.status,
                                             response=body,
                                             headers=headers)

                    # Get code value from location parameters
                    query = headers['Location'].split("?")[1]
                    params = {x[0]: x[1] for x in [x.split("=") for x in query.split("&")]}
                    return params['code']
