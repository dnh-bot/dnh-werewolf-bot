from game.roles.villager import Villager


class Seer(Villager):
    # Seer can check 1 person each night to see if they are villager/werewolf

    def on_night(self):
        # poll_result = self.vote()
        # if poll_result is not None:
        #     client.message(client.get_personal_channel(self.player_id), isinstance(game.get_player(poll_result.id), Werewolf))
        pass
