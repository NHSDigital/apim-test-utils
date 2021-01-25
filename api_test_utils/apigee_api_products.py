from api_test_utils.apigee_api import ApigeeApi
from api_test_utils.api_session_client import APISessionClient


class ApigeeApiProducts(ApigeeApi):
    """ A simple class to help facilitate CRUD operations for products in Apigee """

    def __init__(self, org_name: str = "nhsd-nonprod"):
        super().__init__(org_name)

        # Default product properties
        self.scopes = []
        self.environments = ["internal-dev"]
        self.access = "public"
        self.rate_limit = "10ps"
        self.proxies = []
        self.attributes = [
            {"name": "access", "value": self.access},
            {"name": "ratelimit", "value": self.rate_limit}
        ]
        self.quota = 500
        self.quota_interval = "1"
        self.quota_time_unit = "minute"

    def _product(self):
        return {
            "apiResources": [],
            "approvalType": "auto",
            "attributes": self.attributes,
            "description": "",
            "displayName": self.name,
            "name": self.name,
            "environments": self.environments,
            "quota": self.quota,
            "quotaInterval": self.quota_interval,
            "quotaTimeUnit": self.quota_time_unit,
            "scopes": self.scopes,
            "proxies": self.proxies
        }

    def update_ratelimits(self, quota: int, quota_interval: str, quota_time_unit: str, rate_limit: str):
        """ Update the product set quota values """
        self.quota = quota
        self.quota_interval = quota_interval
        self.quota_time_unit = quota_time_unit
        self.rate_limit = rate_limit
        self.attributes[1]["value"] = rate_limit
        return self._update_product()

    def update_attributes(self, attributes: dict):
        """ Update the product attributes """
        updated_attributes = [
            {"name": "access", "value": self.access},
            {"name": "ratelimit", "value": self.rate_limit}
        ]
        for key, value in attributes.items():
            updated_attributes.append({"name": key, "value": value})
        self.attributes = updated_attributes
        return self._update_product()

    def update_environments(self, environments: list):
        """ Update the product environments """
        permitted_environments = ["internal-dev", "internal-dev-sandbox", "internal-qa", "internal-qa-sandbox", "ref"]
        if not set(environments) <= set(permitted_environments):
            raise Exception(f"Failed updating environments! specified environments not permitted: {environments}"
                            f"\n Please specify valid environments: {permitted_environments}")
        self.environments = environments
        return self._update_product()

    def update_scopes(self, scopes: list):
        """ Update the product scopes """
        self.scopes = scopes
        return self._update_product()

    def update_proxies(self, proxies: list):
        """ Update the product assigned proxies """
        self.proxies = proxies
        return self._update_product()

    async def create_new_product(self) -> dict:
        """ Create a new developer product in apigee """
        async with APISessionClient(self.base_uri) as session:
            async with session.post("apiproducts",
                                    headers=self.headers,
                                    json=self._product()) as resp:

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

    async def _update_product(self) -> dict:
        """ Update product """
        async with APISessionClient(self.base_uri) as session:
            async with session.put(f"apiproducts/{self.name}",
                                   headers=self.headers,
                                   json=self._product()) as resp:
                body = await resp.json()
                if resp.status != 200:
                    headers = dict(resp.headers.items())
                    self._throw_friendly_error(message=f"unable to update product: {self._product}",
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
