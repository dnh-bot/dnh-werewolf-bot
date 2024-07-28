import text_templates
from config import *
from game.modes.new_moon.events import *
from game.modes.new_moon.events.no_event import NoEvent


class NewMoonMode:
    def __init__(self, is_on=False):
        self.is_on = is_on
        self.current_event = NoEvent

    def turn_on(self):
        self.is_on = True
        self.set_random_event()

    def turn_off(self):
        self.is_on = False
        self.current_event = NoEvent

    def set_random_event(self):
        if self.is_on:
            while True:
                next_event = generate_random_event()
                if next_event.KEY != self.current_event.KEY:
                    self.current_event = next_event
                    break
        else:
            self.current_event = NoEvent

    def get_current_event(self):
        assert self.is_on or self.current_event is NoEvent
        return self.current_event

    async def announce_current_event(self, interface):
        if self.is_on:
            await interface.send_action_text_to_channel(
                f"new_moon_{'no' if self.current_event is NoEvent else 'special'}_event_text",
                GAMEPLAY_CHANNEL,
                event_name=get_event_name(self.current_event),
                event_description=get_event_description(self.current_event)
            )

    async def do_new_daytime_phase(self, interface, **kwargs):
        if self.is_on:
            await self.announce_current_event(interface)
            return await self.current_event.on_day_start(interface, **kwargs)

        return None

    async def do_end_daytime_phase(self, interface, **kwargs):
        if self.is_on:
            return await self.current_event.on_day_end(interface, **kwargs)

        return None

    async def do_new_nighttime_phase(self, interface, **kwargs):
        if self.is_on:
            await self.announce_current_event(interface)
            return await self.current_event.on_night_start(interface, **kwargs)

        return None

    async def do_end_nighttime_phase(self, interface, **kwargs):
        if self.is_on:
            return await self.current_event.on_night_end(interface, **kwargs)

        return None

    async def do_action(self, interface, **kwargs):
        if self.is_on:
            return await self.current_event.do_action(interface, **kwargs)

        return None

    @classmethod
    def active_in_event(cls, valid_event, valid_phase=None):
        def wrapper(cmd_func):
            async def execute(game, author, *a, **kw):
                game_current_event = game.new_moon_mode.get_current_event()

                if game_current_event is not valid_event or (valid_phase is not None and game.game_phase != valid_phase):
                    event_title = get_event_name(valid_event)
                    if valid_phase:
                        phase_str = text_templates.get_word_in_language(str(valid_phase))
                        return text_templates.generate_text(
                            "invalid_in_event_phase_text", event=event_title, phase=phase_str
                        )

                    return text_templates.generate_text("invalid_in_event_text", event=event_title)

                return await cmd_func(game, author, *a, **kw)

            return execute

        return wrapper

    @classmethod
    def deactivate_in_event(cls, invalid_event=None):
        def wrapper(cmd_func):
            async def execute(game, author, *a, **kw):
                game_current_event = game.new_moon_mode.get_current_event()

                if invalid_event and game_current_event is invalid_event:
                    # event_title = "" if invalid_event is None else invalid_event.get_name()
                    # return text_templates.generate_text("invalid_out_event_text", event=event_title)
                    return await game_current_event.do_action(game.interface)

                return await cmd_func(game, author, *a, **kw)

            return execute

        return wrapper
