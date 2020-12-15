import pytest
from api_test_utils.apigee_api import ApigeeApiDeveloperApps


@pytest.fixture()
def _api():
    """Create Apigee Instance"""
    api = ApigeeApiDeveloperApps()
    return api


@pytest.fixture()
@pytest.mark.asyncio
async def setup(_api):
    """Setup and Teardown, create an app at the start and then destroy it at the end"""
    print("Creating Test App..")
    await _api.create_new_app(app_name="auto_generated_app_by_apim_test_utils",
                              attributes=[{'name': 'Test', 'value': ''}])

    yield
    # Teardown
    print("Destroying Test App..")
    await _api.destroy_app(app_name="auto_generated_app_by_apim_test_utils")


@pytest.mark.asyncio
@pytest.mark.usefixtures('setup')
async def test_apigee_get_custom_attributes(_api):
    resp = await _api.get_custom_attributes(app_name='auto_generated_app_by_apim_test_utils')
    assert resp['attribute'] == [
        {'name': 'DisplayName', 'value': 'auto_generated_app_by_apim_test_utils'},
        {'name': 'Test', 'value': ''}
    ]


@pytest.mark.asyncio
@pytest.mark.usefixtures('setup')
async def test_apigee_update_custom_attribute(_api):
    resp = await _api.update_custom_attribute(app_name='auto_generated_app_by_apim_test_utils',
                                              attribute_name="Test",
                                              attribute_value="Passed")
    assert resp == {'name': 'Test', 'value': 'Passed'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('setup')
async def test_apigee_delete_custom_attributes(_api):
    resp = await _api.delete_custom_attribute(app_name='auto_generated_app_by_apim_test_utils',
                                              attribute_name='Test')
    assert resp == {'name': 'Test', 'value': ''}


@pytest.mark.asyncio
@pytest.mark.usefixtures('setup')
async def test_apigee_add_api_product_to_app(_api):
    resp = await _api.add_api_product(app_name='auto_generated_app_by_apim_test_utils',
                                      api_products=["internal-testing-internal-dev"])
    assert resp == [{'apiproduct': 'internal-testing-internal-dev', 'status': 'approved'}]


@pytest.mark.asyncio
@pytest.mark.usefixtures('setup')
async def test_apigee_get_app_keys(_api):
    credentials = await _api.get_app_keys(app_name='auto_generated_app_by_apim_test_utils')
    assert len(credentials['client_id']) == 32
    assert len(credentials['client_secret']) == 16


@pytest.mark.asyncio
@pytest.mark.usefixtures('setup')
async def test_apigee_get_call_back_url(_api):
    callback_url = await _api.get_callback_url(app_name='auto_generated_app_by_apim_test_utils')
    assert callback_url == "http://example.com"
