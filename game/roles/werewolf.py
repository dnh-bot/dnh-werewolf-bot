from villager import Villager
from character import CharacterStatus

import client
import game


class Werewolf(Villager):
    # Werewolf is also a Villager at day, but has ability to vote at night
    # Do nothing actually, at night, a poll will be shown in #werewolf channel for all werewolves to vote there instead

    def on_night(self):
        if self.status == CharacterStatus.ALIVE:
            client.unmute(self.player)  # unmute Village on day for disscussion

        # vote
        poll_id = client.show_poll(client.get_personal_channel(self.player), game.get_alive_players())
        await timeout() or get_poll_result(poll_id)
