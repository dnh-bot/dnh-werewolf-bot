import asyncio
import commands
import text_templates


class ConsoleInterface:
    def __init__(self, guild=None):
        self.guild = guild  # Unused

    async def send_text_to_channel(self, msg, channel_name):
        print(f"#{channel_name}: {msg}")
        return True

    async def send_embed_to_channel(self, embed_msg, channel_name):
        print(f"#{channel_name}: {embed_msg}")
        return True

    async def create_channel(self, channel_name):
        print(f"{channel_name} created!")
        return True

    async def delete_channel(self, channel_name):
        print(f"{channel_name} deleted!")
        return True

    async def add_user_to_channel(self, player_id, channel_name, is_read=True, is_send=True):
        print(f"Added {player_id} to channel #{channel_name} {is_read} {is_send}")
        return True


class DiscordInterface:
    def __init__(self, guild, client):
        self.guild = guild
        self.client = client

    async def send_action_text_to_channel(self, action, channel_name, **kwargs):
        return await self.send_text_to_channel(text_templates.generate_text(action, **kwargs), channel_name)

    async def send_text_to_channel(self, msg, channel_name):
        return await commands.admin.send_text_to_channel(self.guild, msg, channel_name)

    async def send_embed_to_channel(self, embed_msg, channel_name):
        return await commands.admin.send_embed_to_channel(self.guild, embed_msg, channel_name)

    async def create_channel(self, channel_name):
        return await commands.admin.create_channel(self.guild, self.client.user, channel_name)

    async def delete_channel(self, channel_name):
        return await commands.admin.delete_channel(self.guild, self.client.user, channel_name)

    async def add_user_to_channel(self, player_id, channel_name, is_read=True, is_send=True):
        return await commands.admin.add_user_to_channel(self.guild, self.client.get_user(player_id), channel_name, is_read, is_send)
