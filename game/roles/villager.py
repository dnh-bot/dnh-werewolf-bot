from character import Character, CharacterStatus

import client
import game


class Villager(Character):
    def on_role(self):
        poll_id = client.show_poll(client.get_personal_channel(self.player), game.get_alive_players())
        await timeout() or get_poll_result(poll_id)

    def on_day(self):
        if self.status == CharacterStatus.ALIVE:
            client.unmute(self.player)  # unmute Village on day for discussion

    def on_night(self):
        client.mute(self.player)  # mute Village on night
