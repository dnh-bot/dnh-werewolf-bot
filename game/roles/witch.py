from game.roles.character import CharacterStatus
from game.roles.villager import Villager


class Witch(Villager):
    # Witch can reborn a dead player 1 time in a game

    def __init__(self, interface, player_id, player_name, status=CharacterStatus.ALIVE):
        super().__init__(interface, player_id, player_name, status)
        self.power = 1
        self.curse_power = 1

    @classmethod
    def new(cls, interface, player_id, status, **kwargs):
        obj = cls(interface, player_id, interface.get_user_display_name(player_id), status)
        if "power" in kwargs:
            obj.power, obj.curse_power = map(int, kwargs["power"][1:-1].split(","))

        return obj

    def get_power(self):
        return self.power

    def on_use_power(self):
        self.power = 0

    def get_curse_power(self):
        return self.curse_power

    def on_use_curse_power(self):
        self.curse_power = 0

    async def on_night(self):
        pass

    async def on_action(self, embed_data):
        await self.interface.send_action_text_to_channel("witch_before_voting_text", self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.player_id},{self.status.value},power=({self.power},{self.curse_power}))"
