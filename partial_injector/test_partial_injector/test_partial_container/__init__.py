from importlib.metadata import distributions, version

installed_packages = {dist.metadata['Name'] for dist in distributions()}
if "test_sversion" in installed_packages:
    __version__ = version("test_partial_injector")
else:
    __version__ = "0.0.0"

__author__ = "kostiantyn.chomakov@gmail.com"

from . import test_case_injected_async_output,\
              test_case_multiple_registrations_same_key,\
              test_case_inject_items

__all__ = ['test_case_injected_async_output',
           'test_case_multiple_registrations_same_key',
           'test_case_inject_items']