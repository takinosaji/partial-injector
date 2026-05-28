class VersionNotFoundError(Exception):
    """Raised when the version cannot be located in the file-system search path."""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


VersionNotFoundException = VersionNotFoundError
