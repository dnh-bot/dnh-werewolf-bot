from villager import Villager

import client
import game


class Seer(Villager):
    # Seer can check 1 person each night to see if they are villager/werewolf

    def on_role(self):
        poll_id = client.show_poll(client.get_personal_channel(self.player), game.get_alive_players())
        poll_result = get_poll_result(poll_id)
        if poll_result:
            client.message(client.get_personal_channel(self.player), isinstance(game.get_player(poll_result.id), Werewolf))
