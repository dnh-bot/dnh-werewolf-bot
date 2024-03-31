import asyncio
from enum import Enum

import text_templates
from game import const
import config

BANNED_CHARS = "`!@#$%^&*()\'\"#/\\<>[]()|{}?+=,."


class CharacterStatus(Enum):
    ALIVE = 1
    KILLED = 2
    PROTECTED = 3


class Character:
    def __init__(self, interface, player_id, player_name):
        self.interface = interface
        self.player_id = player_id
        self.status = CharacterStatus.ALIVE
        self.player_name = player_name
        # channel_name MUST BE lowercase!
        player_name = player_name.replace("-", " ")
        valid_channel_name = "".join(c for c in player_name if c not in BANNED_CHARS).lower()
        valid_channel_name = "-".join(valid_channel_name.split())
        self.channel_name = f"{config.PERSONAL}-{valid_channel_name}"
        self.target = None

    def get_role(self):
        return self.__class__.__name__

    def is_alive(self):
        return self.status != CharacterStatus.KILLED

    async def get_killed(self, is_suicide=False):
        # Suicide means the couple follows lover death
        if self.status == CharacterStatus.KILLED or (self.status == CharacterStatus.PROTECTED and not is_suicide):
            return False
        self.status = CharacterStatus.KILLED
        # Mute player in config.GAMEPLAY_CHANNEL
        await asyncio.gather(
            self.interface.add_user_to_channel(self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=False),
            self.interface.add_user_to_channel(self.player_id, config.CEMETERY_CHANNEL, is_read=True, is_send=True),
            # Welcome text in Cemetery
            self.interface.send_action_text_to_channel(
                "after_death_text", config.CEMETERY_CHANNEL, user=f"<@{self.player_id}>"),
            self.interface.add_user_to_channel(self.player_id, config.COUPLE_CHANNEL, is_read=False, is_send=False)
        )
        return True

    async def on_reborn(self):
        if self.status == CharacterStatus.ALIVE:
            return False
        self.status = CharacterStatus.ALIVE
        await asyncio.gather(
            self.interface.add_user_to_channel(self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True),
            self.interface.add_user_to_channel(self.player_id, config.CEMETERY_CHANNEL, is_read=False, is_send=False),
            self.interface.send_action_text_to_channel(
                "after_reborn_text", config.GAMEPLAY_CHANNEL, user=f"<@{self.player_id}>")
        )

    def get_protected(self):
        self.status = CharacterStatus.PROTECTED

    def get_target(self):
        return self.target

    def set_target(self, target_id):
        self.target = target_id

    def generate_invalid_target_text(self, target_id):
        pass

    def register_target(self, target):
        target_id = target.player_id

        invalid_target_text = self.generate_invalid_target_text(target_id)
        if invalid_target_text:
            return invalid_target_text

        self.set_target(target_id)
        return text_templates.generate_text(f"{self.get_role()}_after_voting_text", target=f"<@{target_id}>")

    async def create_personal_channel(self, self_check=False):
        await self.interface.create_channel(self.channel_name)
        await self.interface.add_user_to_channel(self.player_id, self.channel_name, is_read=True, is_send=True)
        if not self_check:
            await self.interface.send_action_text_to_channel(
                "personal_channel_welcome_text", self.channel_name,
                player_id=self.player_id, player_role=self.get_role()
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

        if phase == const.GamePhase.DAY:
            await self.on_day()  # Special skill here
        elif phase == const.GamePhase.NIGHT:
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
