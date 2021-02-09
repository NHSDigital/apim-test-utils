from time import sleep
import pytest
from api_test_utils.apigee_api_trace import ApigeeApiTraceDebug
from api_test_utils.oauth_helper import OauthHelper
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps
from api_test_utils.apigee_api_proxies import ApigeeApiProxies


@pytest.mark.asyncio
@pytest.yield_fixture(scope='function')
async def _api():
    """ Setup and Teardown """

    api = ApigeeApiTraceDebug(proxy="personal-demographics-pr-538")

    print(f"\nStarting Trace on proxy {api.proxy}...")
    await api.start_trace()

    yield api
    # teardown
    try:
        print(f"\nStopping Trace on proxy {api.proxy}...")
        await api.stop_trace()
    except RuntimeError:
        # Session already stopped or has timed out
        pass


@pytest.mark.asyncio
async def test_apigee_get_trace_data():
    api = ApigeeApiTraceDebug(proxy='apim-test')
    await api.start_trace()
    resp = await api.get_trace_data()
    assert resp == {}


@pytest.mark.asyncio
async def test_apigee_get_trace_without_data(_api):
    resp = await _api.get_trace_data()
    assert resp is None


@pytest.mark.asyncio
async def test_apigee_stop_trace(_api):
    resp = await _api.stop_trace()
    assert resp['status_code'] == 200
    assert resp['body']['name'] == _api.name


@pytest.mark.asyncio
async def test_apigee_stop_trace_without_starting_trace():
    api = ApigeeApiTraceDebug(proxy="personal-demographics-pr-538")
    with pytest.raises(RuntimeError) as exec_info:
        await api.stop_trace()
        assert str(exec_info.value) == 'You must run start_trace() before you can run stop_trace()'


@pytest.mark.asyncio
async def test_apigee_trace_timeout():
    api = ApigeeApiTraceDebug(proxy="personal-demographics-pr-538", timeout=2)
    resp = await api.start_trace()
    assert resp['status_code'] == 201

    with pytest.raises(TimeoutError) as exec_info:
        sleep(2)  # Wait for session to timeout
        await api.get_trace_data()
        assert str(exec_info.value) == "Your session has timed out, please rerun the start_trace() method again"
