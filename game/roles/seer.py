
import client
import game

class Seer(VVillage): # Seer can check 1 person each night to see if they are village/werewolf

    def on_role(self):
        poll_id = client.show_poll(client.get_personal_channel(self.player), game.alive_players())
        poll_result = got_poll_result(poll_id)
        if poll_result:
            client.message(client.get_personal_channel(self.player), game.get_player(poll_result.id) is Werewolf)


