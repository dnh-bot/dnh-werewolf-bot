# pylint: disable=too-many-instance-attributes
"""
Module containing the Gist object
"""
from __future__ import annotations

import typing
from typing import Optional, Dict, List
import datetime

from .file import File
from .constants import TIME_FORMAT, GIST_URL_REGEX

if typing.TYPE_CHECKING:
    from .client import Client


__all__ = ("Gist",)


class Gist:
    """The Gist object that represents a gist"""

    __slots__ = (
        "client",
        "comments",
        "comments_url",
        "commits_url",
        "_created_at",
        "_description",
        "description",
        "_files",
        "files",
        "forks",
        "forks_url",
        "git_pull_url",
        "git_push_url",
        "history",
        "url",
        "id",
        "node_id",
        "owner",
        "public",
        "truncated",
        "_updated_at",
        "api_url",
        "user",
    )

    def __init__(self, data: Dict, client: Client):
        self.client = client

        self._update_attrs(data)

    def __eq__(self, other):
        """Equality comparison. Compares:
        - Types of the two objects
        - Description of the two Gist objects
        - Files of the two Gist objects
            - Files' names
            - Files' contents
        """
        if not (
            isinstance(other, Gist)
            and self.description == other.description
            and len(self.files) == len(other.files)
        ):
            return False

        for self_file, other_file in zip(self.files, other.files):
            if self_file != other_file:
                return False
        return True

    def _update_attrs(self, data: Dict):
        """Update the Gist object's attributes with the provided data"""

        self.comments: int = data.get("comments", None)
        self.comments_url: str = data.get("comments_url", None)
        self.commits_url: str = data.get("commits_url", None)
        self._created_at: str = data.get("created_at", None)
        self._description: str = data.get("description", None)
        self._files: Dict = data.get("files", None)
        self.forks: List = data.get("forks", None)  # TODO Fork object
        self.forks_url: str = data.get("forks_url", None)
        self.git_pull_url: str = data.get("git_pull_url", None)
        self.git_push_url: str = data.get("git_push_url", None)
        self.history: List = data.get("history", None)  # TODO History object
        self.url: str = data.get("html_url", None)
        self.id: str = data.get("id", None)
        self.node_id: str = data.get("node_id", None)
        self.owner: Dict = data.get("owner", None)  # TODO User object
        self.public: bool = data.get("public", None)
        self.truncated: bool = data.get("truncated", None)
        self._updated_at: str = data.get("updated_at", None)
        self.api_url: str = data.get("url", None)
        self.user: None = data.get("user", None)

        self.description: str = self._description
        self.files: List[File] = File.from_dict(self._files)

    @staticmethod
    def _get_dt_obj(time: str) -> datetime.datetime:
        """Internal method to convert string datetime format to datetime object"""
        time = time + " +0000"  # Tells datetime that the timezone is UTC
        dt_obj: datetime.datetime = datetime.datetime.strptime(time, TIME_FORMAT)
        return dt_obj

    @property
    def created_at(self) -> datetime.datetime:
        return self._get_dt_obj(self._created_at)

    @created_at.setter
    def created_at(self, value: str):
        self._created_at = value

    @property
    def updated_at(self) -> datetime.datetime:
        return self._get_dt_obj(self._updated_at)

    @updated_at.setter
    def updated_at(self, value: str):
        self._updated_at = value

    async def update(self):
        """Fetch and update the Gist object with the gist"""

        updated_gist_data = await self.client.update_gist(self.id)
        self._update_attrs(updated_gist_data)

    async def edit(
        self, *, description: Optional[str] = None, files: Optional[List[File]] = None
    ):
        """Edit the gist associated with the Gist object, then update the Gist object"""

        # Since both files and description are optional arguments,
        # you can edit a file through Gist.files (e.g. Gist.files[0].content = "Edited content")
        # or the description through Gist.description (e.g. Gist.description = "Edited description")
        # and then call Gist.edit() without passing any args to sync the gist with the changed values.
        if not description:
            description = self.description

        if not files:
            files = self.files

        files_dict = {}
        for file in files:
            # Update the files_dict with the dictionaries of each File object
            files_dict.update(file.to_dict())
        # If there are no changes, the gist will not edit
        if all(
            (
                self.description == self._description,
                files_dict == self._files,
            )
        ):
            return

        kwargs = {"description": description, "files": files}

        edited_gist_data = await self.client.edit_gist(self.id, **kwargs)
        self._update_attrs(edited_gist_data)

    async def delete(self):
        """Delete the gist associated with the Gist object, then delete the Gist object itself"""

        await self.client.delete_gist(self.id)

    @staticmethod
    def gist_url_to_id(url_or_id: str) -> str:
        """Function to get a gist's ID from its url, or assumes that the input was the ID itself if it is not a url"""

        match = GIST_URL_REGEX.search(url_or_id)
        if match:
            url_or_id = match.group("gist_id") or match.group("gist_id2")

        return url_or_id
