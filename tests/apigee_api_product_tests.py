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


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_update_product_attributes(_api):
    resp = await _api.update_attributes(attributes={"Test": "Passed"})
    assert resp['attributes'][1] == {'name': 'Test', 'value': 'Passed'}


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_update_product_proxies(_api):
    resp = await _api.update_proxies(
        proxies=["identity-service-internal-dev"]
    )
    assert resp['proxies'] == ["identity-service-internal-dev"]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_update_product_scopes(_api):
    resp = await _api.update_scopes(
        scopes=["test_scope:USER-RESTRICTED"]
    )
    assert resp['scopes'] == ["test_scope:USER-RESTRICTED"]


@pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_update_quota_values(_api):
    resp = await _api.update_ratelimits(
        quota=600,
        quota_interval="1",
        quota_time_unit="minute",
        ratelimit="15ps"
    )
    print(resp)
    assert resp['quota'] == '600'
    assert resp['quotaInterval'] == '1'
    assert resp['quotaTimeUnit'] == 'minute'
    assert resp['attributes'][1]["value"] == "15ps"



@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_product_environments_updates(_api):
    resp = await _api.update_environments(
        environments=["internal-dev", "internal-qa"]
    )
    assert resp['environments'] == ["internal-dev", "internal-qa"]
