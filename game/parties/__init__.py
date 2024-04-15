import asyncio


class Party:
    def __init__(self, interface, channel_name, welcome_text_label):
        self.interface = interface
        self.channel_name = channel_name
        self.welcome_text_label = welcome_text_label

        self.player_set = set()

    def reset_state(self):
        self.player_set = set()

    async def create_channel(self):
        await self.interface.create_channel(self.channel_name)

    async def delete_channel(self):
        await self.interface.delete_channel(self.channel_name)

    async def mute_channel(self, is_muted):
        if self.interface.guild:
            alive_members = list(set(member.id for member in self.interface.guild.members) & self.player_set)
        else:
            alive_members = []

        print("Party alive_members =", alive_members)
        await asyncio.gather(*[
            self.interface.add_user_to_channel(_id, self.channel_name, is_read=True, is_send=not is_muted)
            for _id in alive_members
        ])

    def get_all_players(self):
        return sorted(self.player_set)

    async def add_player(self, player_id):
        print("parties add_player")
        self.player_set.add(player_id)
        await self.interface.add_user_to_channel(player_id, self.channel_name, is_read=True, is_send=True)

    async def send_welcome_text(self, player_id=None):
        print("parties send_welcome_text")
        user_kwargs = {}
        if player_id:
            user_kwargs["user"] = f"<@{player_id}>"
        else:
            for _idx, _player_id in enumerate(self.player_set, 1):
                user_kwargs[f"user{_idx}"] = f"<@{_player_id}>"

        await self.interface.send_action_text_to_channel(self.welcome_text_label, self.channel_name, **user_kwargs)

    async def on_player_killed(self, player_id, phase_str=""):
        if player_id in self.player_set:
            print("on_player_killed phase =", phase_str)
            await self.interface.add_user_to_channel(player_id, self.channel_name, is_read=False, is_send=False)

    async def on_player_reborn(self, player_id):
        if player_id in self.player_set:
            await self.interface.add_user_to_channel(player_id, self.channel_name, is_read=True, is_send=True)

    def __contains__(self, player_id):
        return player_id in self.player_set
