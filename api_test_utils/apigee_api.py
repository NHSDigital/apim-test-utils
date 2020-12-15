from typing import List
from os import environ
from api_test_utils.api_session_client import APISessionClient


class ApigeeApiDeveloperApps:
    """ A simple class to help facilitate CRUD operations for developer apps in Apigee """

    def __init__(self, org_name: str = "nhsd-nonprod", developer_email: str = "apm-testing-internal-dev@nhs.net"):
        self.org_name = org_name
        self.developer_email = developer_email

        self.base_uri = "https://api.enterprise.apigee.com/v1/organizations/" \
                        f"{self.org_name}/developers/{self.developer_email}"

        self.default_params = {
            "org_name": self.org_name,
            "developer_email": self.developer_email,
        }

        self.headers = {'Authorization': f"Bearer {self._get_token()}"}

    @staticmethod
    def _get_token():
        _token = environ.get('APIGEE_API_TOKEN', 'not-set').strip()
        if _token == 'not-set':
            raise Exception('\nAPIGEE_API_TOKEN is missing from environment variables\n'
                            'If you do not have a token please follow the instructions in the link below:\n'
                            r'https://docs.apigee.com/api-platform/system-administration/using-gettoken'
                            '\n')
        return _token

    @staticmethod
    def _throw_friendly_error(message: str, url: str, status_code: int, response: str, headers: dict) -> Exception:
        raise Exception(f"\n{'*' * len(message)}\n"
                        f"MESSAGE: {message}\n"
                        f"URL: {url}\n"
                        f"STATUS CODE: {status_code}\n"
                        f"RESPONSE: {response}\n"
                        f"HEADERS: {headers}\n"
                        f"{'*' * len(message)}\n")

    @staticmethod
    def _verify_attributes(attributes: List[dict]):
        """Only 'name and 'value' are accepted as valid keys"""
        for key in [attribute.keys() for attribute in attributes]:
            if key != {'name', 'value'}:
                Exception('\nAttributes in incorrect format. '
                          'Please follow convention: List[ dict{ "name": str, "value": str } ... ]\n')

    async def create_new_app(self, app_name: str, attributes: List[dict] = None,
                             callback_url: str = "http://example.com") -> dict:
        """
        app_name: name of the application you want to create.
        attributes: a list of custom attributes and values e.g. [{"name": str, "value": str}]
        callback_url: the callback URL for the new app.
        """

        if attributes is not None:
            self._verify_attributes(attributes)
        else:
            attributes = []

        attributes.append({"name": "DisplayName", "value": app_name})

        data = {
            "attributes": attributes,
            "callbackUrl": callback_url,
            "name": app_name,
            "status": "approved"
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.post("apps",
                                    params=self.default_params,
                                    headers=self.headers,
                                    json=data) as resp:

                if resp.status in {401, 502}:  # 401 is an expired token while 502 is an invalid token
                    raise Exception("Your token has expired or is invalid")

                body = await resp.json()
                if resp.status == 409:
                    # allow the code to continue instead of throwing an error
                    print(f'The app "{app_name}" already exists!')
                elif resp.status != 201:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to create app: {app_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def add_api_product(self, app_name: str, api_products: list) -> dict:
        """ Add a number of API Products to an app """
        params = self.default_params.copy()
        params['app_name'] = app_name

        data = {
            "apiProducts": api_products,
            "name": app_name,
            "status": "approved"
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.put(f"apps/{app_name}",
                                   params=params,
                                   headers=self.headers,
                                   json=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to add api products {api_products} to app: {app_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body['credentials'][0]['apiProducts']

    async def update_custom_attribute(self, app_name: str, attribute_name: str, attribute_value: str) -> dict:
        """ Update an existing custom attribute """
        params = self.default_params.copy()
        params["app_name"] = app_name
        params["attribute_name"] = attribute_name

        data = {
            "value": attribute_value
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.post(f"apps/{app_name}/attributes/{attribute_name}",
                                    params=params,
                                    headers=self.headers,
                                    json=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to add custom attribute for app: {app_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def delete_custom_attribute(self, app_name: str, attribute_name: str) -> dict:
        """ Delete a custom attribute """
        params = self.default_params.copy()
        params["app_name"] = app_name
        params["attribute_name"] = attribute_name

        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"apps/{app_name}/attributes/{attribute_name}",
                                      params=params,
                                      headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to delete custom attribute for app: {app_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def get_custom_attributes(self, app_name: str) -> dict:
        """ Get the list of custom attributes assigned to an app """
        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"apps/{app_name}/attributes", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to get custom attribute for app: {app_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def get_app_details(self, app_name: str) -> dict:
        """ Return all available details for an app """
        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"apps/{app_name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to get app details for: {app_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def get_app_keys(self, app_name: str) -> dict:
        """ Returns an apps client id and client secret """
        resp = await self.get_app_details(app_name)
        credentials = resp['credentials'][0]
        client_id = credentials['consumerKey']
        secret_key = credentials['consumerSecret']
        return {'client_id': client_id, 'client_secret': secret_key}

    async def get_callback_url(self, app_name: str) -> str:
        """ Get the callback url for a given app """
        resp = await self.get_app_details(app_name)
        return resp['callbackUrl']

    async def destroy_app(self, app_name: str) -> dict:
        """ Delete an app """
        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"apps/{app_name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to delete app: {app_name}, PLEASE DELETE MANUALLY",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body
