import os
from setuptools import setup, find_namespace_packages

setup_py_path = os.path.abspath(__file__)
setup_py_dir_path = os.path.abspath(os.path.dirname(setup_py_path))
version_file_name = "VERSION.txt"
version_file_path = f"{setup_py_dir_path}/../{version_file_name}"

setup(
    name='partial-injector',
    version=open(version_file_path).read().strip(),
    author='Kostiantyn Chomakov',
    author_email='kostiantyn.chomakov@gmail.com',
    description='Dependency Injection for FP',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/takinosaji/partial-injector',
    include_package_data=True,
    package_data={'': [version_file_name]},
    packages=find_namespace_packages(where='..',
                                     include=['partial_injector',
                                              'partial_injector.*'],
                                     exclude=['partial_injector.demo']),
    package_dir={'': '..'},
    install_requires=[
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: MIT',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.13'
)