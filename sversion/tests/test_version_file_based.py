import os
import pytest
from unittest.mock import patch, mock_open

from sversion.version_file_based import get_version, VersionNotFoundException

@pytest.fixture
def mock_os_path_exists():
    with patch('os.path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_open_version_file():
    with patch('builtins.open', mock_open(read_data='1.0.0')) as mock_file:
        yield mock_file

@pytest.fixture
def mock_open_custom_version_file():
    with patch('builtins.open', mock_open(read_data='2.0.0')) as mock_file:
        yield mock_file

def test_get_version_found_with_folder_path(mock_os_path_exists, mock_open_version_file):
    mock_os_path_exists.side_effect = lambda path: path.endswith('VERSION.txt')
    assert get_version(os.path.abspath(os.path.dirname(__file__))) == '1.0.0'

def test_get_version_found_with_file_path(mock_os_path_exists, mock_open_version_file):
    mock_os_path_exists.side_effect = lambda path: path.endswith('VERSION.txt')
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dummy_file.py')
    assert get_version(file_path) == '1.0.0'

def test_get_version_not_found(mock_os_path_exists):
    mock_os_path_exists.return_value = False
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)))

def test_get_version_permission_error(mock_os_path_exists):
    mock_os_path_exists.side_effect = PermissionError
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)))

def test_get_version_with_custom_file_name_found(mock_os_path_exists, mock_open_custom_version_file):
    mock_os_path_exists.side_effect = lambda path: path.endswith('CUSTOM_VERSION.txt')
    assert get_version(os.path.abspath(os.path.dirname(__file__)), version_file_name="CUSTOM_VERSION.txt") == '2.0.0'

def test_get_version_with_custom_file_name_not_found(mock_os_path_exists):
    mock_os_path_exists.return_value = False
    with pytest.raises(VersionNotFoundException):
        get_version(os.path.abspath(os.path.dirname(__file__)), version_file_name="CUSTOM_VERSION.txt")