import commands
import text_templates


class ConsoleInterface:
    def __init__(self, category=None):
        self.category = category  # Unused

    async def send_action_text_to_channel(self, action, channel_name, **kwargs):
        await self.send_text_to_channel(text_templates.generate_text(action, **kwargs), channel_name)
        return True

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

    def get_channel_mention(self, channel_name):
        return f"#{channel_name}"


class DiscordInterface:
    def __init__(self, category, client):
        self.category = category
        self.client = client

    async def send_action_text_to_channel(self, action, channel_name, **kwargs):
        return await self.send_text_to_channel(text_templates.generate_text(action, **kwargs), channel_name)

    async def send_text_to_channel(self, msg, channel_name):
        return await commands.admin.send_text_to_channel(self.category, msg, channel_name)

    async def send_embed_to_channel(self, embed_msg, channel_name):
        return await commands.admin.send_embed_to_channel(self.category, embed_msg, channel_name)

    async def create_channel(self, channel_name):
        return await commands.admin.create_channel(self.category, self.client.user, channel_name)

    async def delete_channel(self, channel_name):
        return await commands.admin.delete_channel(self.category, self.client.user, channel_name)

    async def add_user_to_channel(self, player_id, channel_name, is_read=True, is_send=True):
        return await commands.admin.add_user_to_channel(self.category, self.client.get_user(player_id), channel_name, is_read, is_send)

    def get_channel_mention(self, channel_name):
        channel = commands.admin.get_channel_in_category(self.category, channel_name)
        if channel:
            return f"<#{channel.id}>"

        return f"#{channel_name}"
