from enum import Enum

import game
import config

BANNED_CHARS = '`!@#$%^&*()\'\"#/\\<>[]()|{}?+=,.'

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
        valid_channel_name = "".join(c for c in player_name if c not in BANNED_CHARS).lower()
        self.channel_name = f"personal-{'-'.join(valid_channel_name.split())}"


    def is_alive(self):
        return self.status != CharacterStatus.KILLED


    async def get_killed(self):
        if self.status == CharacterStatus.PROTECTED:
            return False
        self.status = CharacterStatus.KILLED
        # Mute player in config.GAMEPLAY_CHANNEL
        await self.interface.add_user_to_channel(self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=False)
        return True


    def get_protected(self):
        self.status = CharacterStatus.PROTECTED


    async def create_personal_channel(self):
        await self.interface.create_channel(self.channel_name)
        await self.interface.add_user_to_channel(self.player_id, self.channel_name, is_read=True, is_send=True)
        await self.interface.send_text_to_channel(
            f"Welcome <@{self.player_id}> to the game!\nYour role is {self.__class__.__name__}", self.channel_name
        )
        print("Created channel", self.channel_name)


    async def send_to_personal_channel(self, text):
        await self.interface.send_text_to_channel(text, self.channel_name)


    async def delete_personal_channel(self):
        await self.interface.delete_channel(self.channel_name)


    async def on_phase(self, phase):
        self.status = CharacterStatus.ALIVE
        if phase == game.GamePhase.DAY:
            # Unmute all players in config.GAMEPLAY_CHANNEL
            await self.interface.add_user_to_channel(
                self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True
            )
            await self.on_day()  # Special skill here
        elif phase == game.GamePhase.NIGHT:
            # Mute all players in config.GAMEPLAY_CHANNEL
            await self.interface.add_user_to_channel(
                self.player_id, config.GAMEPLAY_CHANNEL, is_read=True, is_send=False
            )
            await self.on_night()  # Special skill here


    async def on_day(self):  # Will be overload in Child Class
        pass


    async def on_night(self):  # Will be overload in Child Class
        pass


    async def on_action(self, embed_data): # Will be overload in Child Class
        pass
