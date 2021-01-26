import jwt  # pyjwt
from os import environ
from uuid import uuid4
from time import time
from . import throw_friendly_error
from api_test_utils.api_session_client import APISessionClient
from aiohttp.client_exceptions import ContentTypeError


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
            raise Exception('\nOAUTH_PROXY is missing from environment variables\n')
        return _proxy

    def _get_base_uri(self):
        _uri = environ.get('OAUTH_BASE_URI', 'not-set').strip()
        if _uri == 'not-set':
            raise Exception('\nOAUTH_BASE_URI is missing from environment variables\n')
        return f"{_uri}/{self.proxy}"

    @staticmethod
    def _get_private_key():
        _path = environ.get("JWT_PRIVATE_KEY_ABSOLUTE_PATH", 'not-set').strip()
        if _path == 'not-set':
            raise Exception("\nJWT_PRIVATE_KEY_ABSOLUTE_PATH is missing from environment variables\n")
        with open(_path, "r") as f:
            contents = f.read()
        if not contents:
            raise Exception("Contents of file empty. Check JWT_PRIVATE_KEY_ABSOLUTE_PATH.")
        return contents

    async def get_authenticated_with_simulated_auth(self) -> str:
        """Get the code parameter value required to post to the oauth /token endpoint"""
        authenticator = _SimulatedAuthFlow(self.base_uri, self.client_id, self.redirect_uri)
        return await authenticator.authenticate()

    async def _get_default_authorization_code_request_data(self, timeout: int = 5000, refresh_token: str = "") -> dict:
        """Get the default data required for a authorization code request"""
        form_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': "authorization_code",
        }
        if refresh_token != "":
            form_data['refresh_token'] = refresh_token
            form_data['_refresh_token_expiry_ms'] = timeout
        else:
            form_data['redirect_uri'] = self.redirect_uri
            form_data['code'] = await self.get_authenticated_with_simulated_auth()
            form_data['_access_token_expiry_ms'] = timeout
        return form_data

    @staticmethod
    async def _get_default_client_credentials_request_data(jwt: bytes) -> dict:
        """Get the default data required for a client credentials request"""
        return {
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt,
            "grant_type": "client_credentials",
        }

    async def hit_oauth_endpoint(self, method: str, endpoint: str, **kwargs) -> dict:
        """Send a request to a OAuth endpoint"""
        async with APISessionClient(self.base_uri) as session:
            request_method = (session.post, session.get)[method.lower().strip() == 'get']
            async with request_method(endpoint, **kwargs) as resp:
                try:
                    body = await resp.json()
                    _ = body.pop('message_id', None)  # Remove the unique message id if the response is na error
                except ContentTypeError:
                    # Might be html or text response
                    body = resp.read()

                return {'method': resp.method, 'url': resp.url, 'status_code': resp.status, 'body': body,
                        'headers': dict(resp.headers.items()), 'history': resp.history}

    async def get_token_response(self, grant_type: str = 'authorization_code',
                                 request_data: dict = None, **kwargs) -> dict:
        if not request_data:
            # Get defaults
            func = {
                'authorization_code': self._get_default_authorization_code_request_data,
                'client_credentials': self._get_default_client_credentials_request_data,
            }.get(grant_type)

            request_data = await func(**kwargs)
        return await self.hit_oauth_endpoint("post", "token", data=request_data)

    def create_jwt(self, kid: str, signing_key: str = None, claims: dict = None, algorithm: str = "RS512") -> bytes:
        """Create a Json Web Token"""
        if not signing_key:
            # Get default key
            signing_key = self._get_private_key()

        if not claims:
            # Get default claims
            claims = {
                "sub": self.client_id,
                "iss": self.client_id,
                "jti": str(uuid4()),
                "aud": f"{self.base_uri}/token",
                "exp": int(time()) + 5,
            }

        additional_headers = ({}, {"kid": kid})[kid is not None]
        return jwt.encode(claims, signing_key, algorithm=algorithm, headers=additional_headers)


class _SimulatedAuthFlow:
    def __init__(self, base_uri: str, client_id: str, redirect_uri: str):
        self.base_uri = base_uri
        self.client_id = client_id
        self.redirect_uri = redirect_uri

    async def _get_state(self, request_state: str) -> str:
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
                        raise Exception("unexpected response, unable to authenticate with simulated oauth")

                    url = headers['Location'].split("?")[1]
                    params = {x[0]: x[1] for x in [x.split("=") for x in url.split("&")]}
                    return params['code']
