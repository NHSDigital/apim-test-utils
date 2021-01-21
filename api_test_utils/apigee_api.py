from os import environ
from uuid import uuid4


class ApigeeApi(object):
    """ A simple class to help facilitate CRUD operations in Apigee """

    def __init__(self, org_name: str = "nhsd-nonprod"):
        self.org_name = org_name
        self.name = f"apim-auto-${uuid4().hex}"
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
