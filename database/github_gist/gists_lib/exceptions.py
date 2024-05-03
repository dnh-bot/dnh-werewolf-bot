# pylint: disable=unnecessary-pass
"""
Module containing the exceptions that the wrapper uses
"""


from typing import Optional, Union, Dict, Any

import aiohttp

__all__ = (
    "ClientException",
    "HTTPException",
    "AuthorizationFailure",
    "NotFound",
)


class GistsException(Exception):
    """Base exception class"""

    pass


class ClientException(GistsException):
    """Exception that is raised when an operation in the Client class fails"""

    pass


class GistException(GistsException):
    """Exception that is raised when an operation in the Client class fails"""

    pass


class HTTPException(ClientException):
    """Exception that is raised for HTTP request related failures"""

    def __init__(
        self,
        response: aiohttp.ClientResponse,
        data: Optional[Union[str, Dict[str, Any]]],
    ):
        self.response: aiohttp.ClientResponse = response
        self.status: int = response.status
        self.code: int
        self.text: str

        if isinstance(data, dict):
            self.code = data.get("code", 0)

            self.text = data.get("message", "")
        else:
            self.text = data or ""
            self.code = 0

        message = f"{self.response.status} {self.response.reason} ({self.code})"
        if len(self.text):
            message += f": {self.text}"

        super().__init__(message)


class AuthorizationFailure(ClientException):
    """Exception that is raised when authorizing provided token in the Client class fails."""

    pass


class NotFound(HTTPException):
    """HTTPException that is raised when the status code is 404"""

    pass


class DataFetchError(ClientException):
    """Exception that is raised when fetching data fails."""

    pass
