import json
from database.github_gist import gists_lib


class GitHubGist:
    def __init__(self, personal_access_token, gist_id_url):
        self.client = gists_lib.Client()
        self.personal_access_token = personal_access_token
        self.gist_id_url = gist_id_url

    async def authorize(self):
        await self.client.authorize(self.personal_access_token)

    async def verify_gist(self):
        try:
            await self.authorize()

            await self.client.get_gist(self.gist_id_url)

            return True
        except Exception as e:
            print("Init Github Gist failed, please check GITHUB_GIST_ID_URL and GITHUB_GIST_TOKEN or remove/comment them in .env file")
            print(f"Github Gist error: {e}")
            return False

    async def get_gist(self, file_name=None):
        try:
            if not file_name:
                return

            await self.authorize()

            gist = await self.client.get_gist(self.gist_id_url)

            for file in gist.files:
                if file.name == file_name:
                    return json.loads(file.content)

            return {}
        except Exception as e:
            print("Error in get_gist: ", e)
            return {}

    async def edit_gist(self, file_name=None, updating_content=None):
        try:
            if not (file_name or updating_content):
                return

            await self.authorize()

            files = [
                gists_lib.File(name=file_name, content=json.dumps(updating_content)),
            ]

            await self.client.edit_gist(self.gist_id_url, files=files)
        except Exception as e:
            print("Error in edit_gist:", e)
