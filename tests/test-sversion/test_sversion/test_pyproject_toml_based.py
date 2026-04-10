import os
import pytest
from unittest.mock import patch, mock_open

from sversion.pyproject_toml_based import get_version, VersionNotFoundException

@pytest.fixture
def mock_os_path_exists():
    with patch('os.path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_open_pyproject_toml():
    valid_toml_content = """
    [tool.poetry]
    version = "1.2.3"
    """
    with patch('builtins.open', mock_open(read_data=valid_toml_content)) as mock_file:
        yield mock_file

@pytest.fixture
def mock_open_uv_project_file():
    uv_toml_content = """
    [project]
    name = "my-package"
    version = "3.1.4"
    """
    with patch('builtins.open', mock_open(read_data=uv_toml_content)) as mock_file:
        yield mock_file

@pytest.fixture
def mock_open_no_version_section():
    no_version_toml_content = """
    [build-system]
    requires = ["setuptools"]
    """
    with patch('builtins.open', mock_open(read_data=no_version_toml_content)) as mock_file:
        yield mock_file

@pytest.fixture
def mock_open_custom_project_file():
    custom_toml_content = """
    [tool.poetry]
    version = "2.0.0"
    """
    with patch('builtins.open', mock_open(read_data=custom_toml_content)) as mock_file:
        yield mock_file

def test_get_version_found_with_folder_path(mock_os_path_exists, mock_open_pyproject_toml):
    mock_os_path_exists.side_effect = lambda path: path.endswith('pyproject.toml')
    assert get_version(os.path.abspath(os.path.dirname(__file__))) == "1.2.3"

def test_get_version_found_with_file_path(mock_os_path_exists, mock_open_pyproject_toml):
    mock_os_path_exists.side_effect = lambda path: path.endswith('pyproject.toml')
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dummy_file.py')
    assert get_version(file_path) == "1.2.3"

def test_get_version_not_found(mock_os_path_exists):
    mock_os_path_exists.return_value = False
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)))

def test_get_version_permission_error(mock_os_path_exists):
    mock_os_path_exists.side_effect = PermissionError
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)))

def test_get_version_with_custom_project_file_found(mock_os_path_exists, mock_open_custom_project_file):
    mock_os_path_exists.side_effect = lambda path: path.endswith('custom_project.toml')
    assert get_version(os.path.abspath(os.path.dirname(__file__)), project_file_name="custom_project.toml") == "2.0.0"

def test_get_version_with_custom_project_file_not_found(mock_os_path_exists):
    mock_os_path_exists.return_value = False
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)), project_file_name="custom_project.toml")

def test_get_version_found_in_project_section(mock_os_path_exists, mock_open_uv_project_file):
    mock_os_path_exists.side_effect = lambda path: path.endswith('pyproject.toml')
    assert get_version(os.path.abspath(os.path.dirname(__file__))) == "3.1.4"

def test_get_version_project_section_takes_precedence_over_poetry(mock_os_path_exists):
    toml_content = """
    [project]
    version = "4.0.0"

    [tool.poetry]
    version = "1.0.0"
    """
    with patch('builtins.open', mock_open(read_data=toml_content)):
        mock_os_path_exists.side_effect = lambda path: path.endswith('pyproject.toml')
        assert get_version(os.path.abspath(os.path.dirname(__file__))) == "4.0.0"

def test_get_version_not_found_when_no_known_section(mock_os_path_exists, mock_open_no_version_section):
    mock_os_path_exists.side_effect = lambda path: path.endswith('pyproject.toml')
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)))