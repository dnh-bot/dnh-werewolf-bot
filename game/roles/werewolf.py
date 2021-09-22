import config
from game.roles.villager import Villager
from game.roles.character import CharacterStatus


class Werewolf(Villager):
    # Werewolf is also a Villager at day, but has ability to vote at night
    # Do nothing actually, at night, a poll will be shown in #werewolf channel for all werewolves to vote there instead
    async def get_killed(self):
        if await super(Werewolf, self).get_killed():
            await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=False, is_send=False)
            return True
        else:
            return False

    async def on_reborn(self):
        await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)
 

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return True
