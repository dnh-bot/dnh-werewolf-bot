from game.roles.villager import Villager


class Guard(Villager):
    # Guard is basic Villager with ability to protect one person each night

    async def on_night(self):
        # poll_id = client.show_poll(client.get_personal_channel(self.player_id), game.get_alive_players())
        # await timeout() or get_poll_result(poll_id)
        pass


    async def on_action(self, embed_data):
        await self.interface.send_embed_to_channel(embed_data, self.channel_name)