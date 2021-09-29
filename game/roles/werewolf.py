import config
from game.roles.character import Character


class Werewolf(Character):
    # Werewolf is able to vote at day, but has ability to vote at night
    # Do nothing actually, at night, a poll will be shown in #werewolf channel for all werewolves to vote there instead

    @classmethod
    def get_character_description(cls):
        return "Werewolf - Sói. Có thể vote vào ban ngày như dân. Ban đêm chọn ra một người để giết."

    async def get_killed(self):
        if await super(Werewolf, self).get_killed():
            await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=False, is_send=False)
            return True
        return False

    async def on_reborn(self):
        await self.interface.add_user_to_channel(self.player_id, config.WEREWOLF_CHANNEL, is_read=True, is_send=True)

    async def on_night(self):
        pass

    def seer_seen_as_werewolf(self):
        return True
