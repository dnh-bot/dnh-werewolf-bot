import config
from game.roles.character import Character


class Werewolf(Character):
    # Werewolf is able to vote at day, but has ability to vote at night
    # Do nothing actually, at night, a poll will be shown in #werewolf channel for all werewolves to vote there instead

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Werewolf

    async def get_killed(self, is_suicide=False):
        if await super().get_killed(is_suicide):
            await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=False, is_send=False)
            return True
        return False

    async def on_reborn(self):
        await super().on_reborn()
        await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)

    async def on_start_game(self, *_):
        await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)
        await self.interface.send_action_text_to_channel("werewolf_welcome_text", config.WEREWOLF_CHANNEL, user=f"<@{self.player_id}>")

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return True
