from game.roles.villager import Villager

import game


class Doctor(Villager):
    # Doctor is basic Villager with ability to protect one person each night

    def on_role(self):
        # poll_id = client.show_poll(client.get_personal_channel(self.player), game.get_alive_players())
        # await timeout() or get_poll_result(poll_id)
        pass
