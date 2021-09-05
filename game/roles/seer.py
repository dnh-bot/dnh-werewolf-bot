from game.roles.villager import Villager


class Seer(Villager):
    # Seer can check 1 person each night to see if they are villager/werewolf

    async def on_night(self):
        await self.send_to_personal_channel("Đêm nay tiên tri muốn soi ai?")
