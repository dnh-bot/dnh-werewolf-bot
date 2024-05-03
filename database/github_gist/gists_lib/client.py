# pylint: disable=too-many-arguments, no-else-return, raise-missing-from
"""
Module containing the main Client class used to send requests
"""


from typing import Optional, Dict, List
import sys

import aiohttp

from .gist import Gist
from .file import File
from .exceptions import HTTPException, AuthorizationFailure, NotFound
from .constants import API_URL


__all__ = ("Client",)


class Client:
    """Does not take access token directly to allow actions that do not require authorization.

    Use the authorize method to authorize
    """

    def __init__(self):
        self.access_token = None  # Set by Client.authorize()

        self.user_data = None

    async def authorize(self, access_token: str):
        """Method used to authorize the client,
        In order to send requests that need authorization
        """

        self.access_token = access_token

        # TODO User object rather than the raw json data
        self.user_data = await self.fetch_user_data()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        data=None,
        headers=None,
        authorization: bool = True,
    ) -> Dict:
        """The method to make asynchronous requests to the GitHub API"""

        headers_final = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": (
                f"Gists.py (https://github.com/witherredaway/gists.py) "
                f"Python/{sys.version_info[0]}.{sys.version_info[1]} aiohttp/{aiohttp.__version__}"
            ),
        }
        if authorization:
            if not self.access_token:
                raise AuthorizationFailure(
                    "To use functions that require authorization, "
                    "please authorize the Client with Client.authorize"
                )
            headers_final["Authorization"] = f"token {self.access_token}"

        request_url = f"{API_URL}/{url}"

        if headers is not None and isinstance(headers, dict):
            headers_final.update(headers)

        async with aiohttp.ClientSession() as session:
            response = await session.request(
                method, request_url, params=params, json=data, headers=headers_final
            )

            try:
                data = await response.json()
            except aiohttp.client_exceptions.ContentTypeError:
                data = response.content

            remaining = response.headers.get("X-Ratelimit-Remaining")

            if 300 > response.status >= 200:
                return data
            elif response.status == 429 or remaining == "0":
                raise HTTPException(response, data)
            elif response.status == 404:
                raise NotFound(response, data)
            elif response.status == 401:
                raise AuthorizationFailure(
                    "Invalid personal access token has been passed."
                )

    async def fetch_user_data(self) -> Dict:
        """Fetch data of the authenticated user"""

        try:
            # TODO User object rather than the raw json data
            user_data: Dict = await self.request("GET", "user", authorization=True)
        except NotFound as error:
            raise NotFound(error.response, "User not found")

        return user_data

    async def fetch_gist_data(self, gist_id: str) -> Dict:
        """Fetch data of a Gist"""

        try:
            gist_data: Dict = await self.request(
                "GET", f"gists/{gist_id}", authorization=True
            )
        except NotFound as error:
            raise NotFound(error.response, "Gist not found")
        return gist_data

    async def get_gist(self, gist_url_or_id: str) -> Gist:
        """Get a Gist object representing the gist associated with the provided gist ID or url

        Does not require authorization.
        """

        gist_id = Gist.gist_url_to_id(gist_url_or_id)

        data = await self.fetch_gist_data(gist_id)
        return Gist(data, self)

    async def create_gist(
        self,
        *,
        files: List[File],
        description: str = None,
        public: bool = True,
    ) -> Gist:
        """Create a new gist and return a Gist object associated with that gist"""

        files_dict = {}
        for file in files:
            # Update the files_dict with the dictionaries of each File object
            files_dict.update(file.to_dict())

        data = {"public": public, "files": files_dict}
        params = {"scope": "gist"}

        if description:
            data["description"] = description

        gist_data = await self.request("POST", "gists", data=data, params=params)
        return Gist(gist_data, self)

    async def update_gist(self, gist_url_or_id: str):
        """Alias of fetch_gist_data, used to fetch a gist's data."""

        gist_id = Gist.gist_url_to_id(gist_url_or_id)

        updated_gist_data = await self.fetch_gist_data(gist_id)
        return updated_gist_data

    async def edit_gist(
        self,
        gist_url_or_id: str,
        *,
        description: Optional[str] = None,
        files: Optional[List[File]] = None,
    ) -> Dict:
        """Edit the gist associated with the provided gist id, and return the edited data"""

        gist_id = Gist.gist_url_to_id(gist_url_or_id)

        data = {}

        if files:
            files_dict = {}
            for file in files:
                # Update the files_dict with the dictionaries of each File object
                files_dict.update(file.to_dict())
            data["files"] = files_dict

        if description:
            data["description"] = description

        try:
            edited_gist_data = await self.request(
                "PATCH", f"gists/{gist_id}", data=data
            )
        except NotFound as error:
            raise NotFound(error.response, "Gist not found")
        return edited_gist_data

    async def delete_gist(self, gist_url_or_id: str):
        """Delete the gist associated with the provided gist id"""

        gist_id = Gist.gist_url_to_id(gist_url_or_id)

        try:
            await self.request("DELETE", f"gists/{gist_id}")
        except NotFound as error:
            raise NotFound(error.response, "Gist not found")
