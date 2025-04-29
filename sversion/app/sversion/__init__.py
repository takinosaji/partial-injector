from importlib.metadata import distributions, version

installed_packages = {dist.metadata['Name'] for dist in distributions()}
if "test_sversion" in installed_packages:
    __version__ = version("test_sversion")
else:
    __version__ = "0.0.0"

__author__ = "kostiantyn.chomakov@gmail.com"

from . import file_based, error_handling, contracts

__all__ = ['file_based',
           'error_handling',
           'contracts']