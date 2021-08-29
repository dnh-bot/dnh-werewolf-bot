
import client

class Village(Character):
    def on_day(self):
        if self.status == 'alive':
            client.unmute(self.player) # unmute Village on day for disscussion

    def on_vote(self):
        poll_id = client.show_poll(client.get_personal_channel(self.player), game.get_alive_players())
        await timeout() or got_result(poll_id)

    def on_night(self):
        client.mute(self.player) # mute Village on night

    def on_role(self):
        pass # Villager simply do not have any special role to act
