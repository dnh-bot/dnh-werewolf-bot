
import client

class Doctor(Village): # Doctor is basic Villager with ability to protect one person each night

    def on_role(self):
        poll_id = client.show_poll(client.get_personal_channel(self.player), game.alive_players())
        await timeout() or got_poll_result(poll_id)


