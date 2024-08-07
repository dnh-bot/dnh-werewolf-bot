from game.roles.character import Character
from game.roles.werewolf import Werewolf


class Rat(Character):
    """ 
    Rat is a Werewolf. Rat can not see Werewolf party, and Werewolf party can not see Rat.
    Rat can bite someone. Rat will die if they are a Fox or a Guard.

    If Rat bites Diseased, both will die unless one of them is protected -
    at this case the Rat will only be ill and not die.
    """

    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.party = Werewolf

    async def on_day(self):
        self.target = None

    async def on_night_start(self, alive_embed_data, _):
        if self.is_alive():
            await self.interface.send_action_text_to_channel("rat_before_voting_text", self.channel_name)
            await self.interface.send_embed_to_channel(alive_embed_data, self.channel_name)

    def seer_seen_as_werewolf(self):
        return True
