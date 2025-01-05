from setuptools import setup, find_namespace_packages

setup(
    name='partial-injector',
    version='1.0.0',
    author='Kostiantyn Chomakov',
    author_email='kostiantyn.chomakov@gmail.com',
    description='Dependency Injection for FP',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/takinosaji/partial-injector',
    packages=find_namespace_packages(where='../../',
                                     include=['partial_injector']),
    package_dir={'': '../..'},
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: Syngenta Proprietary',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.13'
)