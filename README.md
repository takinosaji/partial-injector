# partial-injector

Dependency Injection for Functional Programming in Python

# spinq

Simple LINQ in Python

# sversion

Simple versioning for Python projects

## Build and Publish

To build and publish packages in the repository to PyPi, use the following commands:

```powershell
python setup.py sdist bdist_wheel
twine upload .\dist\*
```