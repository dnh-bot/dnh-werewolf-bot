import asyncio
import commands

class ConsoleInterface:
    def __init__(self, guild=None):
        self.guild = guild #Unused

    async def send_text_to_channel(self, msg, channel):
        print("#{channel}: {msg}".format(channel=channel, msg=msg))
        await asyncio.sleep(0)

    async def create_channel(self, channel):
        print("{channel} created!".format(channel=channel))
        await asyncio.sleep(0)

    async def add_user_to_channel(self, player_id, channel):
        print(f"Added {player_id} to channel #{channel}")
        await asyncio.sleep(0)



class DiscordInterface:
    def __init__(self, guild, client):
        self.guild = guild
        self.client = client

    async def send_text_to_channel(self, msg, channel):
        await commands.admin.send_text_to_channel(self.guild, msg, channel)

    async def create_channel(self, channel):
        await commands.admin.create_channel(self.guild, self.client.user, channel)

    async def add_user_to_channel(self, player_id, channel):
        await commands.admin.add_user_to_channel(self.guild, self.client.get_user(player_id), channel)



