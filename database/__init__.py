import os
from config import GITHUB_GIST_ID_URL, GITHUB_GIST_TOKEN
from database.github_gist import GitHubGist
from utils.common import read_json_file, write_json_file


class Database():
    def __init__(self):
        self.github_gist = GitHubGist(GITHUB_GIST_TOKEN, GITHUB_GIST_ID_URL) if (GITHUB_GIST_TOKEN and GITHUB_GIST_ID_URL) else None
        self.data_directory = "json"

    async def verify_init(self):
        return True

    def create_instance(self):
        if self.github_gist:
            print("Using Github Gist Database")
            return GithubGistDatabase()
        print("Using Local File Database")
        return LocalFileDatabase()


class GithubGistDatabase(Database):
    async def verify_init(self):
        print("Verifying Github Gist")
        return await self.github_gist.verify_gist()

    async def read(self, file_name=None):
        gist_data = {}

        gist_data = await self.github_gist.get_gist(file_name)

        return gist_data

    async def update(self, file_name=None, updating_content=None):
        await self.github_gist.edit_gist(file_name, updating_content)


class LocalFileDatabase(Database):
    async def read(self, file_name=None):
        if not file_name:
            return {}

        file_path = os.path.join(self.data_directory, file_name)

        return read_json_file(file_path)

    async def update(self, file_name=None, updating_content=None):
        if not (file_name or updating_content):
            return

        file_path = os.path.join(self.data_directory, file_name)

        write_json_file(file_path, updating_content)
