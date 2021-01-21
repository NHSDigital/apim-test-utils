from os import environ
from uuid import uuid4
from api_test_utils.api_session_client import APISessionClient


class ApigeeApiProducts:
    """ A simple class to help facilitate CRUD operations for products in Apigee """

    def __init__(self, org_name: str = "nhsd-nonprod"):
        self.org_name = org_name
        self.product_name = f"apim-auto-product-${uuid4().hex}"

        # default
        self.scopes = []
        self.environments = ["internal-dev"]

        self.base_uri = f"https://api.enterprise.apigee.com/v1/organizations/{self.org_name}/"

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

    async def create_new_product(self,
                                 quota: int = 300,
                                 quota_interval: str = "1",
                                 quota_time_unit: str = "minute",
                                 access: str = "public",
                                 scopes: list = None,
                                 environments: list = None) -> dict:
        """ Create a new developer product in apigee """

        # override default product properties
        if scopes is not None:
            self.scopes = scopes
        if environments is not None:
            self.environments = environments

        data = {
            "apiResources": [],
            "approvalType": "auto",
            "attributes": [{"name": "access", "value": access}],  # make different access available
            "description": "",
            "displayName": self.product_name,
            "name": self.product_name,
            "environments": ["internal-dev"],
            "quota": quota,
            "quotaInterval": quota_interval,
            "quotaTimeUnit": quota_time_unit,
            "scopes": self.scopes
        }

        print(data)

        async with APISessionClient(self.base_uri) as session:
            async with session.post("apiproducts",
                                    headers=self.headers,
                                    json=data) as resp:

                if resp.status in {401, 502}:  # 401 is an expired token while 502 is an invalid token
                    raise Exception("Your token has expired or is invalid")

                body = await resp.json()
                if resp.status == 409:
                    # allow the code to continue instead of throwing an error
                    print(f'The product "{self.product_name}" already exists!')
                elif resp.status != 201:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to create product: {self.product_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def add_api_proxies(self, api_proxies: list) -> dict:
        """ Add a number of API Products to the app """

        data = {
            "proxies": api_proxies,
            "approvalType": "auto",
            "name": self.product_name,
            "displayName": self.product_name,
            "scopes": self.scopes,
            "environments": self.environments
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.put(f"apiproducts/{self.product_name}",
                                   headers=self.headers,
                                   json=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to add api proxies {api_proxies} to product: "
                                                       f"{self.product_name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body['proxies']

    # async def set_custom_attributes(self, attributes: dict) -> dict:
    #     """ Replaces the current list of attributes with the attributes specified """
    #     custom_attributes = [{"name": "DisplayName", "value": self.product_name}]
    #
    #     for key, value in attributes.items():
    #         custom_attributes.append({"name": key, "value": value})
    #
    #     params = self.default_params.copy()
    #     params['product_name'] = self.product_name
    #
    #     async with APISessionClient(self.base_uri) as session:
    #         async with session.post(f"apps/{self.product_name}/attributes",
    #                                 params=params,
    #                                 headers=self.headers,
    #                                 json={"attribute": custom_attributes}) as resp:
    #             body = await resp.json()
    #             if resp.status != 200:
    #                 headers = dict(resp.headers.items())
    #                 self._throw_friendly_error(message=f"unable to add custom attributes {attributes} to app: "
    #                                                    f"{self.product_name}",
    #                                            url=resp.url,
    #                                            status_code=resp.status,
    #                                            response=body,
    #                                            headers=headers)
    #             return body['attribute']
    #
    # async def update_custom_attribute(self, attribute_name: str, attribute_value: str) -> dict:
    #     """ Update an existing custom attribute """
    #     params = self.default_params.copy()
    #     params["product_name"] = self.product_name
    #     params["attribute_name"] = attribute_name
    #
    #     data = {
    #         "value": attribute_value
    #     }
    #
    #     async with APISessionClient(self.base_uri) as session:
    #         async with session.post(f"apps/{self.product_name}/attributes/{attribute_name}",
    #                                 params=params,
    #                                 headers=self.headers,
    #                                 json=data) as resp:
    #             body = await resp.json()
    #             if resp.status != 200:
    #                 headers = dict(resp.headers.items())
    #                 self._throw_friendly_error(message=f"unable to add custom attribute for app: {self.product_name}",
    #                                            url=resp.url,
    #                                            status_code=resp.status,
    #                                            response=body,
    #                                            headers=headers)
    #             return body

    # async def delete_custom_attribute(self, attribute_name: str) -> dict:
    #     """ Delete a custom attribute """
    #     params = self.default_params.copy()
    #     params["product_name"] = self.product_name
    #     params["attribute_name"] = attribute_name
    #
    #     async with APISessionClient(self.base_uri) as session:
    #         async with session.delete(f"apps/{self.product_name}/attributes/{attribute_name}",
    #                                   params=params,
    #                                   headers=self.headers) as resp:
    #             body = await resp.json()
    #             if resp.status != 200:
    #                 headers = dict(resp.headers.items())
    #                 self._throw_friendly_error(message=f"unable to delete custom attribute for app: {self.product_name}",
    #                                            url=resp.url,
    #                                            status_code=resp.status,
    #                                            response=body,
    #                                            headers=headers)
    #             return body

    # async def get_custom_attributes(self) -> dict:
    #     """ Get the list of custom attributes assigned to the app """
    #     async with APISessionClient(self.base_uri) as session:
    #         async with session.get(f"apps/{self.product_name}/attributes", headers=self.headers) as resp:
    #             body = await resp.json()
    #             if resp.status != 200:
    #                 headers = dict(resp.headers.items())
    #                 self._throw_friendly_error(message=f"unable to get custom attribute for app: {self.product_name}",
    #                                            url=resp.url,
    #                                            status_code=resp.status,
    #                                            response=body,
    #                                            headers=headers)
    #             return body

    # async def get_app_details(self) -> dict:
    #     """ Return all available details for the app """
    #     async with APISessionClient(self.base_uri) as session:
    #         async with session.get(f"apps/{self.product_name}", headers=self.headers) as resp:
    #             body = await resp.json()
    #             if resp.status != 200:
    #                 headers = dict(resp.headers.items())
    #                 self._throw_friendly_error(message=f"unable to get app details for: {self.product_name}",
    #                                            url=resp.url,
    #                                            status_code=resp.status,
    #                                            response=body,
    #                                            headers=headers)
    #             return body

    async def destroy_product(self) -> dict:
        """ Delete the product """
        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"apiproducts/{self.product_name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to delete product: {self.product_name},"
                                                       f" PLEASE DELETE MANUALLY",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body
