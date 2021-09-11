from game.roles.villager import Villager


class Guard(Villager):
    # Guard is basic Villager with ability to protect one person each night

    async def on_night(self):
        # Regain mana
        self.mana = 1

    async def on_action(self, embed_data):
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)
