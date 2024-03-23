from game.roles.villager import Villager


class Seer(Villager):
    # Seer can check 1 person each night to see if they are villager/werewolf

    async def on_night(self):
        # Regain mana
        self.mana = 1

    async def on_action(self, embed_data):
        await self.__class__.send_before_voting_text(self.interface, self.channel_name, "seer")
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)
