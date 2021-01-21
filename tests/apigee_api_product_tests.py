import pytest
from api_test_utils.apigee_api_products import ApigeeApiProducts


@pytest.yield_fixture(scope='function')
@pytest.mark.asyncio
async def _api():
    """ Setup and Teardown, create an product at the start and then destroy it at the end """

    # create apigee instance & attach instance to class
    api = ApigeeApiProducts()

    print("Creating Test Product..")
    await api.create_new_product(scopes=["access_mode:APP-RESTRICTED"])

    yield api
    # teardown
    print("Destroying Test Product..")
    await api.destroy_product()


# @pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
# async def test_apigee_get_custom_attributes(_api):
#     resp = await _api.get_custom_attributes()
#     assert resp['attribute'] == [
#         {'name': 'DisplayName', 'value': _api.app_name},
#     ]


# @pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
# async def test_apigee_add_custom_attribute(_api):
#     resp = await _api.set_custom_attributes(attributes={"Test": "Passed"})
#     assert resp[1] == {'name': 'Test', 'value': 'Passed'}
#
#
# @pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
# async def test_apigee_delete_custom_attributes(_api):
#     resp = await _api.delete_custom_attribute(attribute_name='DisplayName')
#     assert resp == {'name': 'DisplayName', 'value': _api.app_name}
#
#
@pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_add_api_proxy_to_product(_api):
    resp = await _api.add_api_proxies(
        api_proxies=["identity-service-internal-dev"]
    )
    print(resp)
    assert resp == ["identity-service-internal-dev"]
#
#
# @pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
# async def test_apigee_get_app_keys(_api):
#     assert len(_api.get_client_id()) == 32
#     assert len(_api.get_client_secret()) == 16
#
#
# @pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
# async def test_apigee_get_call_back_url(_api):
#     callback_url = await _api.get_callback_url()
#     assert callback_url == "http://example.com"
