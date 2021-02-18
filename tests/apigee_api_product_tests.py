import pytest
from api_test_utils.apigee_api_products import ApigeeApiProducts


@pytest.yield_fixture(scope='function')
@pytest.mark.asyncio
async def _api():
    """ Setup and Teardown, create an product at the start and then destroy it at the end """

    # create apigee instance & attach instance to class
    api = ApigeeApiProducts()

    print("\nCreating Test Product..")
    await api.create_new_product()

    yield api
    # teardown
    print("\nDestroying Test Product..")
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
async def test_apigee_update_product_paths(_api):
    resp = await _api.update_paths(
        paths=["/", "/*"]
    )
    assert resp['apiResources'] == ["/", "/*"]


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
        quota_interval=1,
        quota_time_unit="minute",
        rate_limit="15ps"
    )
    assert resp['quota'] == '600'
    assert resp['quotaInterval'] == '1'
    assert resp['quotaTimeUnit'] == 'minute'
    assert resp['attributes'][1]["value"] == "15ps"


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_product_environments_update(_api):
    resp = await _api.update_environments(
        environments=["internal-dev", "internal-qa"]
    )
    assert resp['environments'] == ["internal-dev", "internal-qa"]


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_invalid_product_environments_update(_api):
    with pytest.raises(RuntimeError):
        await _api.update_environments(["invalid"])


@pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_invalid_quota_time_unit_update(_api):
    with pytest.raises(ValueError):
        await _api.update_ratelimits(quota_time_unit="years")


@pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_invalid_quota_interval_update(_api):
    with pytest.raises(TypeError):
        await _api.update_ratelimits(quota_interval="one")


@pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_invalid_quota_update(_api):
    with pytest.raises(TypeError):
        await _api.update_ratelimits(quota="one")


@pytest.mark.asyncio
# @pytest.mark.skip(reason='waiting for move to azure devops')
async def test_apigee_invalid_ratelimit_update(_api):
    with pytest.raises(ValueError):
        await _api.update_ratelimits(rate_limit="one")
