import config
from game.parties import Party


class CoupleParty(Party):
    allow_reborn_together = False

    def __init__(self, interface, channel_name):
        super().__init__(interface, channel_name, "couple_welcome_text")
        self.cupid_dict = {}

    @staticmethod
    def set_allow_reborn_together(allow_reborn_together):
        CoupleParty.allow_reborn_together = allow_reborn_together

    async def set_couple(self, user1_id, user2_id):
        await self.add_player(user1_id)
        await self.add_player(user2_id)

        self.cupid_dict[user1_id] = user2_id
        self.cupid_dict[user2_id] = user1_id

        print(self.cupid_dict)

    def reset_state(self):
        super().reset_state()
        self.cupid_dict = {}

    def get_couple_target(self, player_id):
        return self.cupid_dict.get(player_id)

    async def on_day_start(self):
        await self.mute_channel(True)

    async def on_night_start(self):
        await self.mute_channel(False)

    async def on_player_killed(self, player_id, phase_str=""):
        if player_id not in self.cupid_dict:
            return

        await super().on_player_killed(player_id, phase_str)
        await super().on_player_killed(self.cupid_dict[player_id], phase_str)

        await self.interface.send_action_text_to_channel(
            f"couple_died_on_{phase_str}_text", config.GAMEPLAY_CHANNEL,
            died_player=f"<@{player_id}>", follow_player=f"<@{self.cupid_dict[player_id]}>"
        )

    async def on_player_reborn(self, player_id):
        if player_id not in self.cupid_dict:
            return

        if CoupleParty.allow_reborn_together:
            await super().on_player_reborn(player_id)
            await super().on_player_reborn(self.cupid_dict[player_id])

            await self.interface.send_action_text_to_channel(
                "couple_reborn_text", self.channel_name,
                player1=f"<@{player_id}>", player2=f"<@{self.cupid_dict[player_id]}>"
            )
            await self.interface.send_action_text_to_channel(
                "couple_reborn_text", config.GAMEPLAY_CHANNEL,
                player1=f"<@{player_id}>", player2=f"<@{self.cupid_dict[player_id]}>"
            )

    def get_players_str(self):
        return " x ".join(f"<@{player_id}>" for player_id in self.cupid_dict)
