import pytest
from api_test_utils.apigee_api import ApigeeApiDeveloperApps


@pytest.yield_fixture(scope='function')
@pytest.mark.asyncio
async def _api():
    """ Setup and Teardown, create an app at the start and then destroy it at the end """

    # create apigee instance & attach instance to class
    api = ApigeeApiDeveloperApps()

    print("Creating Test App..")
    await api.create_new_app()

    yield api
    # teardown
    print("Destroying Test App..")
    await api.destroy_app()


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_get_custom_attributes(_api):
    resp = await _api.get_custom_attributes()
    assert resp['attribute'] == [
        {'name': 'DisplayName', 'value': _api.app_name},
    ]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_add_custom_attribute(_api):
    resp = await _api.set_custom_attributes(attributes={"Test": "Passed"})
    assert resp[1] == {'name': 'Test', 'value': 'Passed'}


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_delete_custom_attributes(_api):
    resp = await _api.delete_custom_attribute(attribute_name='DisplayName')
    assert resp == {'name': 'DisplayName', 'value': _api.app_name}


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_add_api_product_to_app(_api):
    resp = await _api.add_api_product(api_products=["internal-testing-internal-dev"])
    assert resp == [{'apiproduct': 'internal-testing-internal-dev', 'status': 'approved'}]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_get_app_keys(_api):
    credentials = await _api.get_app_keys()
    assert len(credentials['client_id']) == 32
    assert len(credentials['client_secret']) == 16


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_get_call_back_url(_api):
    callback_url = await _api.get_callback_url()
    assert callback_url == "http://example.com"
