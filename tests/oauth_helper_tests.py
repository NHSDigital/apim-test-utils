from random import getrandbits
import pytest
from api_test_utils.oauth_helper import OauthHelper
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps


@pytest.yield_fixture(scope='function')
@pytest.mark.asyncio
async def _test_app():
    """ Setup and Teardown, create an app at the start and then destroy it at the end """

    test_app = ApigeeApiDeveloperApps()

    print("\nCreating Test App..")
    await test_app.create_new_app(callback_url="https://nhsd-apim-testing-internal-dev.herokuapp.com/callback")
    await test_app.add_api_product(["internal-testing-internal-dev"])

    # Set JWT Testing resource url
    await test_app.set_custom_attributes(
        {
            'jwks-resource-url': 'https://nhsdigital.github.io/'
                                 'identity-service-jwks/jwks/'
                                 'internal-dev/'
                                 '9baed6f4-1361-4a8e-8531-1f8426e3aba8.json'
        }
    )

    yield test_app
    # teardown
    print("\nDestroying Test App..")
    await test_app.destroy_app()


@pytest.yield_fixture(scope='function')
def _oauth(_test_app):
    """Return an instance of OauthHelper to the test"""
    return OauthHelper(client_id=_test_app.client_id, client_secret=_test_app.client_secret,
                       redirect_uri=_test_app.callback_url)


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_endpoint(_oauth):
    resp = await _oauth.hit_oauth_endpoint(method="GET", endpoint="authorize", params={
        "client_id": _oauth.client_id,
        "redirect_uri": _oauth.redirect_uri,
        "response_type": "code",
        "state": getrandbits(32)
    })
    assert resp['status_code'] == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_authorization_code(_oauth):
    resp = await _oauth.get_token_response(grant_type='authorization_code')
    assert resp['status_code'] == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_client_credentials(_oauth):
    jwt = _oauth.create_jwt(kid="test-1")
    resp = await _oauth.get_token_response(grant_type='client_credentials', _jwt=jwt)
    assert resp['status_code'] == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_custom_token_request_authorization_code(_oauth):
    resp = await _oauth.get_token_response(grant_type='authorization_code', data={
        'client_id': _oauth.client_id,
        'client_secret': _oauth.client_secret,
        'grant_type': "authorization_code",
        'redirect_uri': "INVALID",
        'code': await _oauth.get_authenticated_with_simulated_auth()
    })
    assert resp['status_code'] == 400
    assert resp['body'] == {'error': 'invalid_request', 'error_description': 'redirect_uri is invalid'}


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_custom_token_request_client_credentials(_oauth):
    jwt = "NotAValidJwt"
    resp = await _oauth.get_token_response(grant_type='client_credentials', data={
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt,
        "grant_type": "client_credentials",
    })
    assert resp['status_code'] == 400
    assert resp['body'] == {
        'error': 'invalid_request',
        'error_description': 'Malformed JWT in client_assertion'
    }


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_refresh_token(_oauth):
    _resp = await _oauth.get_token_response(grant_type='authorization_code')
    resp = await _oauth.get_token_response(grant_type="refresh_token", refresh_token=_resp['body']['refresh_token'])

    assert resp['status_code'] == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_token_exchange(_oauth):
    jwt = _oauth.create_jwt(kid="test-1")
    id_token_jwt = _oauth.create_id_token_jwt()

    resp = await _oauth.get_token_response(grant_type='token_exchange', _jwt=jwt, id_token_jwt=id_token_jwt)
    assert resp['status_code'] == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_custom_token_exchange(_oauth):
    resp = await _oauth.get_token_response(grant_type='token_exchange', data={
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'subject_token_type': 'Invalid',
        'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange'
    })
    assert resp['status_code'] == 400
    assert resp['body'] == {
        'error': 'invalid_request',
        'error_description': "missing or invalid subject_token_type - "
                             "must be 'urn:ietf:params:oauth:token-type:id_token'"
    }


@pytest.mark.asyncio
@pytest.mark.skip(reason='waiting for move to azure devops')
async def test_oauth_missing_argument_token_exchange(_oauth):
    with pytest.raises(TypeError) as exec_info:
        await _oauth.get_token_response(grant_type='token_exchange', _jwt="")
    assert str(exec_info.value) == 'missing 1 required keyword argument: \'id_token_jwt\''
