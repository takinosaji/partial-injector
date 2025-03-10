import os
from setuptools import setup, find_namespace_packages

setup_py_path = os.path.abspath(__file__)
setup_py_dir_path = os.path.abspath(os.path.dirname(setup_py_path))
version_file_name = "VERSION.txt"
version_file_path = f"{setup_py_dir_path}/{version_file_name}"

setup(
    name='test-sversion',
    version=open(version_file_path).read().strip(),
    author='Kostiantyn Chomakov',
    author_email='kostiantyn.chomakov@gmail.com',
    description='Tests for sversion',
    long_description=open(f"{setup_py_dir_path}/README.md").read(),
    long_description_content_type='text/markdown',
    url='https://github.com/takinosaji/partial-injector',
    include_package_data=True,
    package_data={'': [version_file_name]},
    packages=find_namespace_packages(where='..',
                                     include=['test_sversion',
                                              'test_sversion.*']),
    package_dir={'': '..'},
    install_requires=[
        'sversion',
        'pytest',
        'pytest-asyncio'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.13'
)