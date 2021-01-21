import pytest
from api_test_utils.apigee_api_products import ApigeeApiProducts


@pytest.yield_fixture(scope='function')
@pytest.mark.asyncio
async def _api():
    """ Setup and Teardown, create an product at the start and then destroy it at the end """

    # create apigee instance & attach instance to class
    api = ApigeeApiProducts()

    print("Creating Test Product..")
    await api.create_new_product()

    yield api
    # teardown
    print("Destroying Test Product..")
    await api.destroy_product()


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_get_custom_attributes(_api):
    resp = await _api.get_product_details()
    assert resp['attributes'] == [
        {'name': 'access', 'value': _api.access},
    ]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_set_custom_attribute(_api):
    resp = await _api.update_product(attributes={"Test": "Passed"})
    assert resp['attributes'][1] == {'name': 'Test', 'value': 'Passed'}


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_add_api_proxy_to_product(_api):
    resp = await _api.update_product(
        proxies=["identity-service-internal-dev"]
    )
    assert resp['proxies'] == ["identity-service-internal-dev"]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_add_scopes_to_product(_api):
    resp = await _api.update_product(
        scopes=["test_scope:USER-RESTRICTED"]
    )
    assert resp['scopes'] == ["test_scope:USER-RESTRICTED"]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_get_product_details(_api):
    product_details = await _api.get_product_details()
    assert list(product_details.keys()) == ['apiResources',
                                            'approvalType',
                                            'attributes',
                                            'createdAt',
                                            'createdBy',
                                            'description',
                                            'displayName',
                                            'environments',
                                            'lastModifiedAt',
                                            'lastModifiedBy',
                                            'name',
                                            'proxies',
                                            'quota',
                                            'quotaInterval',
                                            'quotaTimeUnit',
                                            'scopes']
