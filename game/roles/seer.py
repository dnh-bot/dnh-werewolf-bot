from game.roles.villager import Villager


class Seer(Villager):
    # Seer can check 1 person each night to see if they are villager/werewolf

    async def on_night(self):
        # Regain mana
        self.mana = 1

    async def on_action(self, embed_data):
        await self.interface.send_action_text_to_channel("seer_before_voting_text", self.channel_name)
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)
