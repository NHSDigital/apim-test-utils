import pytest
from api_test_utils.apigee_api import ApigeeApiDeveloperApps


@pytest.fixture(scope='function')
@pytest.mark.asyncio
async def setup(request):
    """Setup and Teardown, create an app at the start and then destroy it at the end"""

    # create apigee instance & attach instance to class
    api = ApigeeApiDeveloperApps()
    setattr(request.cls, "api", api)

    print("Creating Test App..")
    await api.create_new_app(attributes=[{'name': 'Test', 'value': ''}])

    yield
    # teardown
    print("Destroying Test App..")
    await api.destroy_app()


@pytest.mark.usefixtures("setup")
class TestApigeeApiDeveloperApps:
    """ A test suite to confirm the ASID for a PDS request is behaving as expected """
    def __init__(self):
        self.api = None

    @pytest.mark.asyncio
    async def test_apigee_get_custom_attributes(self):
        resp = await self.api.get_custom_attributes()
        assert resp['attribute'] == [
            {'name': 'DisplayName', 'value': self.api.app_name},
            {'name': 'Test', 'value': ''}
        ]

    @pytest.mark.asyncio
    async def test_apigee_update_custom_attribute(self):
        resp = await self.api.update_custom_attribute(attribute_name="Test", attribute_value="Passed")
        assert resp == {'name': 'Test', 'value': 'Passed'}

    @pytest.mark.asyncio
    async def test_apigee_delete_custom_attributes(self):
        resp = await self.api.delete_custom_attribute(attribute_name='Test')
        assert resp == {'name': 'Test', 'value': ''}

    @pytest.mark.asyncio
    async def test_apigee_add_api_product_to_app(self):
        resp = await self.api.add_api_product(api_products=["internal-testing-internal-dev"])
        assert resp == [{'apiproduct': 'internal-testing-internal-dev', 'status': 'approved'}]

    @pytest.mark.asyncio
    async def test_apigee_get_app_keys(self):
        credentials = await self.api.get_app_keys()
        assert len(credentials['client_id']) == 32
        assert len(credentials['client_secret']) == 16

    @pytest.mark.asyncio
    async def test_apigee_get_call_back_url(self):
        callback_url = await self.api.get_callback_url()
        assert callback_url == "http://example.com"
