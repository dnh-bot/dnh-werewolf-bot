from enum import Enum

import game
import commands

class CharacterStatus(Enum):
    ALIVE = 1
    KILLED = 2
    PROTECTED = 3


class Character:
    def __init__(self, guild, player_id):
        self.guild = guild
        self.player_id = player_id
        self.status = CharacterStatus.ALIVE

    def is_alive(self):
        return self.status == CharacterStatus.ALIVE

    def get_killed(self):
        self.status = CharacterStatus.KILLED

    def action(self):
        pass

    async def create_personal_channel(self):
        self.channel_name = f"personal-{self.player_id}"
        self.member = await self.guild.fetch_member(self.player_id)
        await commands.admin.create_channel(self.guild, self.member, self.channel_name, is_public=False)
        await commands.admin.add_user_to_channel(self.guild, self.member, self.channel_name)
        await commands.admin.send_text_to_channel(self.guild, f"Welcome <@{self.player_id}> to the game!\nYour role is {self.__class__.__name__}", self.channel_name)

    async def send_to_personal_channel(self, text):
        await commands.admin.send_text_to_channel(self.guild, text, self.channel_name)

    async def delete_personal_channel(self):
        await commands.admin.delete_channel(self.guild, self.member, self.channel_name)

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
