from config import GAMEPLAY_CHANNEL
from game.modes.new_moon.events.base import NewMoonEvent


class Somnambulism(NewMoonEvent):
    KEY = "somnambulism"

    @classmethod
    async def on_night_end(cls, interface, **kwargs):
        target = kwargs.get("target")
        if target is None:
            return

        await cls.send_result_text(interface, GAMEPLAY_CHANNEL, target_role=target.get_role())
