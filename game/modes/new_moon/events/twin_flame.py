from game.modes.new_moon.events.base import NewMoonEvent


class TwinFlame(NewMoonEvent):
    KEY = "twin_flame"

    @classmethod
    async def on_night_end(cls, interface, **kwargs):
        await cls.send_announcement_text(interface, interface.config.GAMEPLAY_CHANNEL)
