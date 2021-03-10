from api_test_utils.apigee_api import ApigeeApi
from api_test_utils.api_session_client import APISessionClient
from . import throw_friendly_error


class ApigeeApiDeveloperApps(ApigeeApi):
    """ A simple class to help facilitate CRUD operations for developer apps in Apigee """

    def __init__(self, org_name: str = "nhsd-nonprod", developer_email: str = "apm-testing-internal-dev@nhs.net"):
        super().__init__(org_name)
        self.developer_email = developer_email

        self.client_id = None
        self.client_secret = None
        self.callback_url = None

        self.app_base_uri = f"{self.base_uri}/developers/{self.developer_email}"

        self.default_params = {
            "org_name": self.org_name,
            "developer_email": self.developer_email,
        }

    async def create_new_app(self, callback_url: str = "http://example.com", status: str = "approved") -> dict:
        """ Create a new developer app in apigee """
        self.callback_url = callback_url

        data = {
            "attributes": [{"name": "DisplayName", "value": self.name}],
            "callbackUrl": self.callback_url,
            "name": self.name,
            "status": status
        }

        async with APISessionClient(self.app_base_uri) as session:
            async with session.post("apps",
                                    params=self.default_params,
                                    headers=self.headers,
                                    json=data) as resp:

                if resp.status in {401, 502}:  # 401 is an expired token while 502 is an invalid token
                    raise RuntimeError("Your Apigee token has expired or is invalid")

                body = await resp.json()
                if resp.status == 409:
                    # allow the code to continue instead of throwing an error
                    print(f'The app "{self.name}" already exists!')
                elif resp.status != 201:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to create app: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)

                self.client_id = body["credentials"][0]["consumerKey"]
                self.client_secret = body["credentials"][0]["consumerSecret"]
                return body

    async def add_api_product(self, api_products: list) -> dict:
        """ Add a number of API Products to the app """
        params = self.default_params.copy()
        params['name'] = self.name

        data = {
            "apiProducts": api_products,
            "name": self.name,
            "status": "approved"
        }

        async with APISessionClient(self.app_base_uri) as session:
            async with session.put(f"apps/{self.name}/keys/{self.client_id}",
                                   params=params,
                                   headers=self.headers,
                                   json=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to add api products {api_products} to app: "
                                                 f"{self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body['apiProducts']

    async def set_custom_attributes(self, attributes: dict) -> dict:
        """ Replaces the current list of attributes with the attributes specified """
        custom_attributes = [{"name": "DisplayName", "value": self.name}]

        for key, value in attributes.items():
            custom_attributes.append({"name": key, "value": value})

        params = self.default_params.copy()
        params['name'] = self.name

        async with APISessionClient(self.app_base_uri) as session:
            async with session.post(f"apps/{self.name}/attributes",
                                    params=params,
                                    headers=self.headers,
                                    json={"attribute": custom_attributes}) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to add custom attributes {attributes} to app: "
                                                 f"{self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body['attribute']

    async def update_custom_attribute(self, attribute_name: str, attribute_value: str) -> dict:
        """ Update an existing custom attribute """
        params = self.default_params.copy()
        params["name"] = self.name
        params["attribute_name"] = attribute_name

        data = {
            "value": attribute_value
        }

        async with APISessionClient(self.app_base_uri) as session:
            async with session.post(f"apps/{self.name}/attributes/{attribute_name}",
                                    params=params,
                                    headers=self.headers,
                                    json=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to add custom attribute for app: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def delete_custom_attribute(self, attribute_name: str) -> dict:
        """ Delete a custom attribute """
        params = self.default_params.copy()
        params["name"] = self.name
        params["attribute_name"] = attribute_name

        async with APISessionClient(self.app_base_uri) as session:
            async with session.delete(f"apps/{self.name}/attributes/{attribute_name}",
                                      params=params,
                                      headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to delete custom attribute for app: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def get_custom_attributes(self) -> dict:
        """ Get the list of custom attributes assigned to the app """
        async with APISessionClient(self.app_base_uri) as session:
            async with session.get(f"apps/{self.name}/attributes", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get custom attribute for app: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    async def get_app_details(self) -> dict:
        """ Return all available details for the app """
        async with APISessionClient(self.app_base_uri) as session:
            async with session.get(f"apps/{self.name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to get app details for: {self.name}",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body

    def get_client_id(self):
        """ Get the client id """
        if not self.client_id:
            raise RuntimeError("\nthe application has not been created! \n"
                               "please invoke 'create_new_app()' method before requesting the client_id")
        return self.client_id

    def get_client_secret(self):
        """ Get the client secret """
        if not self.client_secret:
            raise RuntimeError("\nthe application has not been created! \n"
                               "please invoke 'create_new_app()' method before requesting the client secret")
        return self.client_secret

    async def get_callback_url(self) -> str:
        """ Get the callback url """
        if not self.callback_url:
            raise RuntimeError("\nthe application has not been created! \n"
                               "please invoke 'create_new_app()' method before requesting the callback url")
        return self.callback_url

    async def destroy_app(self) -> dict:
        """ Delete the app """
        async with APISessionClient(self.app_base_uri) as session:
            async with session.delete(f"apps/{self.name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    throw_friendly_error(message=f"unable to delete app: {self.name}, PLEASE DELETE MANUALLY",
                                         url=resp.url,
                                         status_code=resp.status,
                                         response=body,
                                         headers=headers)
                return body
