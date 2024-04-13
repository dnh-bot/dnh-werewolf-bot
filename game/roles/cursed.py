from game.roles.villager import Villager
import config


class Cursed(Villager):
    # Cursed is a Villager but will become Werewolf when killed by Werewolf

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.team = Villager


    async def change_team(self, team):
        # pylint: disable=global-statement
        global Cursed
        Cursed = type('Cursed', (team,), dict(Cursed.__dict__))
        self.__class__ = Cursed
        self.team = team
        await self.interface.send_action_text_to_channel("cursed_change_team_text", self.channel_name)
        await self.interface.send_action_text_to_channel("cursed_werewolf_welcome_text", config.WEREWOLF_CHANNEL, user=f"<@{self.player_id}>")


    def get_team_class(self):
        return self.team.__class__.__name__
