import asyncio
import commands

class ConsoleInterface:
    def __init__(self, guild=None):
        self.guild = guild #Unused

    async def send_text_to_channel(self, msg, channel_name):
        print("#{channel}: {msg}".format(channel=channel_name, msg=msg))
        await asyncio.sleep(0)

    async def create_category(self, category_name):
        print("#{category}: {msg}".format(category=category_name))
        await asyncio.sleep(0)

    async def create_channel(self, channel_name):
        print("{channel} created!".format(channel=channel_name))
        await asyncio.sleep(0)

    async def delete_channel(self, channel_name):
        print(f"{channel_name} deleted!")

    async def add_user_to_channel(self, player_id, channel_name):
        print(f"Added {player_id} to channel #{channel_name}")
        await asyncio.sleep(0)


class DiscordInterface:
    def __init__(self, guild, client):
        self.guild = guild
        self.client = client

    async def send_text_to_channel(self, msg, channel_name):
        await commands.admin.send_text_to_channel(self.guild, msg, channel_name)

    async def create_category(self, category_name):
        await commands.admin.create_category(self.guild, self.client.user, category_name)

    async def create_channel(self, channel_name):
        await commands.admin.create_channel(self.guild, self.client.user, channel_name)

    async def delete_channel(self, channel_name):
        await commands.admin.delete_channel(self.guild, self.client.user, channel_name)

    async def add_user_to_channel(self, player_id, channel_name):
        await commands.admin.add_user_to_channel(self.guild, self.client.get_user(player_id), channel_name)



