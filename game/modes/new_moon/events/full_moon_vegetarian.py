from game.modes.new_moon.events.base import NewMoonEvent


class FullMoonVegetarian(NewMoonEvent):
    KEY = "full_moon_vegetarian"

    @classmethod
    async def on_night_start(cls, interface, **kwargs):
        await cls.send_announcement_text(interface, interface.config.WEREWOLF_CHANNEL)

    @classmethod
    async def do_action(cls, interface, **kwargs):
        return cls.get_result_text(**kwargs)
