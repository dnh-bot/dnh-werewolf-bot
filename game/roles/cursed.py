from game.roles.werewolf import Werewolf
from game.roles.villager import Villager
import config

class Cursed(Werewolf):
    def __init__(self, interface, player_id, player_name):
        super().__init__(interface, player_id, player_name)
        self.is_active = False
        self.party = Villager
        self.is_added_to_channel = False

    async def set_active(self, active):
        if self.is_alive() and active != self.is_active:
            if active:
                await self.interface.send_action_text_to_channel("cursed_announce_text", self.channel_name)
                self.party = Werewolf
        self.is_active = active

    async def on_night_start(self):
        if self.is_alive():
            if not self.is_active:
                await self.interface.send_action_text_to_channel("cursed_safe_text", self.channel_name)
                return

            if not self.is_added_to_channel:
                await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)
                await self.interface.send_action_text_to_channel("cursed_welcome_text", config.WEREWOLF_CHANNEL, user=f"<@{self.player_id}>")
                self.is_added_to_channel = True

    def seer_seen_as_werewolf(self):
        return self.is_active
