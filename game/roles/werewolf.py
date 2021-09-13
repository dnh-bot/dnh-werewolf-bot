from game.roles.villager import Villager
from game.roles.character import CharacterStatus


class Werewolf(Villager):
    # Werewolf is also a Villager at day, but has ability to vote at night
    # Do nothing actually, at night, a poll will be shown in #werewolf channel for all werewolves to vote there instead

    async def on_night(self):
        # poll_result = self.vote()
        pass

    def is_werewolf(self):
        return True
