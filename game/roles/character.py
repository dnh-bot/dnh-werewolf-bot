from enum import Enum

import game

class CharacterStatus(Enum):
    ALIVE = 1
    KILLED = 2
    PROTECTED = 3


class Character:
    def __init__(self, interface, player_id):
        self.interface = interface
        self.player_id = player_id
        self.status = CharacterStatus.ALIVE
        self.channel_name = f"personal-{self.player_id}"

    def is_alive(self):
        return self.status == CharacterStatus.ALIVE

    def get_killed(self):
        self.status = CharacterStatus.KILLED

    def action(self):
        pass

    async def create_personal_channel(self):
        channel = await self.interface.create_channel(self.channel_name)
        if channel:
            print("Created channel", channel.name)
            await self.interface.add_user_to_channel(self.player_id, self.channel_name)
            await self.interface.send_text_to_channel(f"Welcome <@{self.player_id}> to the game!\nYour role is {self.__class__.__name__}", self.channel_name)

    async def send_to_personal_channel(self, text):
        await self.interface.send_text_to_channel(text, self.channel_name)

    async def delete_personal_channel(self):
        await self.interface.delete_channel(self.channel_name)

    async def on_phase(self, phase):
        if phase == game.GamePhase.DAY:
            await self.on_day()
        elif phase == game.GamePhase.NIGHT:
            await self.on_night()
        pass

    async def on_day(self):
        pass

    async def on_night(self):
        pass

    def vote(self):
        pass
