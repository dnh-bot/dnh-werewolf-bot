from game.roles.villager import Villager


class Betrayer(Villager):
    # Betrayer is a man but follows Werewolf side. Betrayer knows who are werewolfs but werewolfs didn't know him.

    def seer_seen_as_werewolf(self):
        return False

    async def on_betrayer(self, info):
        await self.interface.send_text_to_channel(info, self.channel_name)
