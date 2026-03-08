# partial-injector

Dependency Injection for Functional Programming in Python

# spinq

Simple LINQ in Python

# sversion

Simple versioning for Python projects

## Build and Publish

To build and publish packages in the repository to PyPi, use the following commands:

```powershell
python -m build (or pyproject-build.exe . on Windows)
twine upload .\dist\*
```

Remember to ensure up-to-date poetry lock files before building and publishing packages. You can do it by running `poetry lock` command in each package directory.