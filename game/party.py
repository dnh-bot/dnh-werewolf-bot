from collections import Counter
from functools import reduce

import text_templates


class Party:
    def __init__(self, interface, channel_name, welcome_text_label):
        self.interface = interface
        self.channel_name = channel_name
        self.welcome_text_label = welcome_text_label

        self.player_set = set()

    async def create_channel(self):
        await self.interface.create_channel(self.channel_name)

    async def delete_channel(self):
        await self.interface.delete_channel(self.channel_name)

    async def add_player(self, player_id):
        print("party add_player")
        self.player_set.add(player_id)
        await self.interface.add_user_to_channel(player_id, self.channel_name, is_read=True, is_send=True)

    async def send_welcome_text(self, player_id=None):
        print("party send_welcome_text")
        user_kwargs = {}
        if player_id:
            user_kwargs["user"] = f"<@{player_id}>"
        else:
            for _idx, _player_id in enumerate(self.player_set, 1):
                user_kwargs[f"user{_idx}"] = f"<@{_player_id}>"

        await self.interface.send_action_text_to_channel(self.welcome_text_label, self.channel_name, **user_kwargs)

    def on_player_killed(self, player_id):
        if player_id in self.player_set:
            self.interface.add_user_to_channel(player_id, self.channel_name, is_read=False, is_send=False)

    def on_player_reborn(self, player_id):
        if player_id in self.player_set:
            self.interface.add_user_to_channel(player_id, self.channel_name, is_read=True, is_send=True)

