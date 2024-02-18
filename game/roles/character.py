import asyncio
from enum import Enum

import game
import config

BANNED_CHARS = "`!@#$%^&*()\'\"#/\\<>[]()|{}?+=,."


class CharacterStatus(Enum):
    ALIVE = 1
    KILLED = 2
    PROTECTED = 3


class Character:
    def __init__(self, interface, player_id, player_name, status=CharacterStatus.ALIVE):
        self.interface = interface
        self.player_id = player_id
        self.status = status
        self.player_name = player_name
        # channel_name MUST BE lowercase!
        player_name = player_name.replace("-", " ")
        valid_channel_name = "".join(c for c in player_name if c not in BANNED_CHARS).lower()
        valid_channel_name = "-".join(valid_channel_name.split())
        self.channel_name = f"personal-{valid_channel_name}"
        self.mana = 0

    @classmethod
    def new(cls, interface, player_id, status, **kwargs):
        obj = cls(interface, player_id, interface.get_user_display_name(player_id), status)
        return obj

    def is_alive(self):
        return self.status != CharacterStatus.KILLED

    async def get_killed(self, is_suicide=False):
        if self.status == CharacterStatus.PROTECTED and not is_suicide:
            return False
        self.status = CharacterStatus.KILLED
        # Mute player in config.GAMEPLAY_CHANNEL
        await asyncio.gather(
            self.interface.add_user_to_channel(self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=False),
            self.interface.add_user_to_channel(self.player_id, config.CEMETERY_CHANNEL, is_read=True, is_send=True),
            self.interface.send_action_text_to_channel("after_death_text", config.CEMETERY_CHANNEL, user=f"<@{self.player_id}>"),
            self.interface.add_user_to_channel(self.player_id, config.COUPLE_CHANNEL, is_read=False, is_send=False)
        )
        return True

    async def on_reborn(self):
        self.status = CharacterStatus.ALIVE
        await asyncio.gather(
            self.interface.add_user_to_channel(self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True),
            self.interface.add_user_to_channel(self.player_id, config.CEMETERY_CHANNEL, is_read=False, is_send=False),
            self.interface.send_action_text_to_channel("after_reborn_text", config.GAMEPLAY_CHANNEL, user=f"<@{self.player_id}>")
        )

    def get_protected(self):
        self.status = CharacterStatus.PROTECTED

    def on_use_mana(self):
        self.mana = 0

    def get_mana(self):
        return self.mana

    async def create_personal_channel(self):
        await self.interface.create_channel(self.channel_name)
        await self.interface.add_user_to_channel(self.player_id, self.channel_name, is_read=True, is_send=True)
        await self.interface.send_action_text_to_channel(
            "personal_channel_welcome_text", self.channel_name,
            player_id=self.player_id, player_role=self.__class__.__name__
        )
        print("Created channel", self.channel_name)

    async def send_to_personal_channel(self, text):
        await self.interface.send_text_to_channel(text, self.channel_name)

    async def delete_personal_channel(self):
        await self.interface.delete_channel(self.channel_name)

    async def on_phase(self, phase):
        # Reset Guard protection
        if self.status == CharacterStatus.PROTECTED:
            self.status = CharacterStatus.ALIVE

        if phase == game.GamePhase.DAY:
            await self.on_day()  # Special skill here
        elif phase == game.GamePhase.NIGHT:
            await self.on_night()  # Special skill here

    async def on_end_game(self):
        # Unmute all players in config.GAMEPLAY_CHANNEL
        await self.interface.add_user_to_channel(
            self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True
        )

    async def on_start_game(self, embed_data):
        # Will be overloaded in Child Class
        pass

    async def on_day(self):
        # Will be overloaded in Child Class
        pass

    async def on_night(self):
        # Will be overloaded in Child Class
        pass

    async def on_action(self, embed_data):
        # Will be overloaded in Child Class
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.player_id},{self.status.value})"
