import os
import pytest
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from selenium import webdriver

from api_test_utils.api_session_client import APISessionClient
from api_test_utils.api_test_session_config import APITestSessionConfig


@pytest.fixture(scope='function')
async def api_client(api_test_config: APITestSessionConfig):

    session_client = APISessionClient(api_test_config.base_uri)

    yield session_client

    await session_client.close()


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(os.path.dirname(__file__), "docker-compose.yml")


@pytest.fixture(scope="session")
def webdriver_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""
    def is_responsive(url):
        try:
            response = requests.get(url)
        except RequestsConnectionError:
            return False
        else:
            body = response.json()
            if body['value']['ready']:
                return True

    print("Starting Webdriver service..")
    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("chromedriver", 4444)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=2, check=lambda: is_responsive(f"{url}/wd/hub/status")
    )
    yield url
    print("Stopping Webdriver service..")


@pytest.fixture(scope="function")
def webdriver_session(webdriver_service):
    try:
        wd = webdriver.Remote(command_executor=f"{webdriver_service}/wd/hub", options=webdriver.ChromeOptions())
    except:
        raise Exception("Could not connect to Chromedriver.")
    else:
        yield wd
    wd.quit()
