"""
Module containing the File object for files in a gist
"""

from typing import Optional, TypeVar, Dict, List


__all__ = ("File",)

F = TypeVar("F", bound="File")


class File:
    """The file object that is provided when editing and creating gists"""

    def __init__(
        self,
        *,
        name: str,
        content: Optional[str] = None,
        new_name: Optional[str] = None
    ):
        self.name: str = name
        self.content: str = content

        self.new_name: str = new_name or self.name

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, File)
            and self.name == other.name
            and self.content == other.content
        )

    def to_dict(self) -> Dict:
        """Returns the dictionary form of the File object"""

        files_dict = {self.name: {"filename": self.new_name}}

        if self.content:
            content_dict = {"content": self.content}
            files_dict[self.name].update(content_dict)

        return files_dict

    @classmethod
    def from_dict(cls, files_dict: Dict) -> List[F]:
        """Returns a list of File objects from a files dictionary"""

        # Example structure of a files_dict:
        #     {
        # "file1.txt": {
        #   "content": ""
        # },
        # "file2.txt": {
        #   "filename": "file2.txt",
        #   "content": "test"
        # },
        # }

        file_objs = []
        for name in files_dict.keys():
            self = cls.__new__(cls)

            self.name = name
            self.content = files_dict[name].get("content", None)
            self.new_name = files_dict[name].get("filename", self.name)

            file_objs.append(self)

        return list(sorted(file_objs, key=lambda f: f.name))
