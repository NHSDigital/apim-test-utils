from api_test_utils.apigee_api import ApigeeApi
from api_test_utils.api_session_client import APISessionClient


class ApigeeApiProducts(ApigeeApi):
    """ A simple class to help facilitate CRUD operations for products in Apigee """

    def __init__(self, org_name: str = "nhsd-nonprod"):
        super().__init__(org_name)

        # default product properties
        self.scopes = []
        self.environments = ["internal-dev"]
        self.access = "public"
        self.proxies = []
        self.attributes = [{"name": "access", "value": self.access}]
        self.quota = 500
        self.quota_interval = "1"
        self.quota_time_unit = "minute"

    def _override_product_properties(self,
                                     quota: int = None,
                                     quota_interval: str = None,
                                     quota_time_unit: str = None,
                                     attributes: dict = None,
                                     access: str = None,
                                     scopes: list = None,
                                     environments: list = None) -> ():
        """ Override any provided product properties """

        # override default product properties
        if scopes is not None:
            self.scopes = scopes
        if environments is not None:
            self.environments = environments
        if access is not None:
            self.access = access
        if quota is not None:
            self.quota = quota
        if quota_interval is not None:
            self.quota_interval = quota_interval
        if quota_time_unit is not None:
            self.quota_time_unit = quota_time_unit
        if attributes is not None:
            custom_attributes = [{"name": "access", "value": self.access}]
            for key, value in attributes.items():
                custom_attributes.append({"name": key, "value": value})
            self.attributes = custom_attributes

    async def create_new_product(self,
                                 quota: int = None,
                                 quota_interval: str = None,
                                 quota_time_unit: str = None,
                                 attributes: dict = None,
                                 access: str = None,
                                 scopes: list = None,
                                 environments: list = None) -> dict:
        """ Create a new developer product in apigee """

        self._override_product_properties(quota, quota_interval, quota_time_unit, attributes, access, scopes,
                                          environments)
        data = {
            "apiResources": [],
            "approvalType": "auto",
            "attributes": self.attributes,  # make different access available
            "description": "",
            "displayName": self.name,
            "name": self.name,
            "environments": ["internal-dev"],
            "quota": self.quota,
            "quotaInterval": self.quota_interval,
            "quotaTimeUnit": self.quota_time_unit,
            "scopes": self.scopes
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.post("apiproducts",
                                    headers=self.headers,
                                    json=data) as resp:

                if resp.status in {401, 502}:  # 401 is an expired token while 502 is an invalid token
                    raise Exception("Your token has expired or is invalid")

                body = await resp.json()
                if resp.status == 409:
                    # allow the code to continue instead of throwing an error
                    print(f'The product "{self.name}" already exists!')
                elif resp.status != 201:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to create product: {self.name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def update_product(self,
                             quota: int = None,
                             quota_interval: str = None,
                             quota_time_unit: str = None,
                             access: str = None,
                             attributes: str = None,
                             scopes: list = None,
                             environments: list = None,
                             api_proxies: list = None) -> dict:
        """ Update product """
        self._override_product_properties(quota, quota_interval, quota_time_unit, attributes, access, scopes,
                                          environments)

        data = {
            "apiResources": [],
            "approvalType": "auto",
            "attributes": self.attributes,  # make different access available
            "description": "",
            "displayName": self.name,
            "name": self.name,
            "environments": environments,
            "quota": quota,
            "quotaInterval": quota_interval,
            "quotaTimeUnit": quota_time_unit,
            "scopes": scopes,
            "proxies": api_proxies
        }

        async with APISessionClient(self.base_uri) as session:
            async with session.put(f"apiproducts/{self.name}",
                                   headers=self.headers,
                                   json=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to add api proxies {api_proxies} to product: "
                                                       f"{self.name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)

                return body

    async def get_product_details(self) -> dict:
        """ Return all available details for the product """
        async with APISessionClient(self.base_uri) as session:
            async with session.get(f"apiproducts/{self.name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to get product details for: {self.name}",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body

    async def destroy_product(self) -> dict:
        """ Delete the product """
        async with APISessionClient(self.base_uri) as session:
            async with session.delete(f"apiproducts/{self.name}", headers=self.headers) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to delete product: {self.name},"
                                                       f" PLEASE DELETE MANUALLY",
                                               url=resp.url,
                                               status_code=resp.status,
                                               response=body,
                                               headers=headers)
                return body
