import os
import api_test_utils


def test_ensure_package_version_set_to_000():
    assert api_test_utils.__version__ == "0.0.0", "packaging is dependant on this being 0.0.0"


def test_ensure_pyproject_version_set_to_000():
    pyproject_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pyproject.toml')
    with open(pyproject_path, 'r') as pyproject_file:
        toml = pyproject_file.read()

        assert "version = \"0.0.0\"" in toml, "packaging is dependant on this being 0.0.0"
