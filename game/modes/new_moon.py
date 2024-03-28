import random

import text_templates
from config import BOT_PREFIX, CEMETERY_CHANNEL, TEXT_LANGUAGE, GAMEPLAY_CHANNEL, WEREWOLF_CHANNEL
import utils

new_moon_event_dict = utils.common.read_json_file("json/new_moon_events_info.json")


class NewMoonMode:
    NO_EVENT = "no_event"
    HEADS_OR_TAILS = "heads_or_tails"
    TWIN_FLAME = "twin_flame"
    SOMNAMBULISM = "somnambulism"
    FULL_MOON_VEGETARIAN = "full_moon_vegetarian"
    PUNISHMENT = "punishment"

    ALL_EVENTS = new_moon_event_dict

    def __init__(self, is_on=False):
        self.is_on = is_on
        self.current_event = NewMoonMode.NO_EVENT

    def turn_on(self):
        self.is_on = True
        self.set_random_event()

    def turn_off(self):
        self.is_on = False
        self.current_event = NewMoonMode.NO_EVENT

    def set_random_event(self):
        self.current_event = self.generate_random_event()

    def generate_random_event(self):
        if self.is_on:
            return random.choices(*zip(*[
                (event_key, event["rate"])
                for event_key, event in new_moon_event_dict.items()
            ]))[0]

        return NewMoonMode.NO_EVENT

    def has_special_event(self):
        return self.current_event != NewMoonMode.NO_EVENT

    def get_current_event_name(self):
        return NewMoonMode.ALL_EVENTS[self.current_event]["title"][TEXT_LANGUAGE]

    def get_current_event_description(self):
        return NewMoonMode.ALL_EVENTS[self.current_event]["description"][TEXT_LANGUAGE]

    def do_coin_toss(self):
        return random.randint(0, 1)

    async def send_result_text(self, interface, channel_name, **kwargs):
        if self.has_special_event():
            await interface.send_action_text_to_channel(
                f"new_moon_{self.current_event}_result_text", channel_name, **kwargs
            )

    async def do_new_daytime_phase(self, interface, **kwargs):
        if self.current_event == NewMoonMode.PUNISHMENT:
            await interface.send_embed_to_channel(kwargs.get("alive_players_embed_data"), CEMETERY_CHANNEL)
            await interface.send_action_text_to_channel("new_moon_punishment_announcement_text", CEMETERY_CHANNEL, cmd_usages=f"`{BOT_PREFIX}punish`")
            return

    async def do_end_nighttime_phase(self, interface, **kwargs):
        if self.current_event == NewMoonMode.TWIN_FLAME:
            await interface.send_action_text_to_channel("new_moon_twin_flame_announcement_text", GAMEPLAY_CHANNEL)
            return

    async def do_action(self, interface, **kwargs):
        if self.current_event == NewMoonMode.HEADS_OR_TAILS:
            await self.do_heads_or_tails_action(interface, kwargs.get("coin_toss_value"))
            return

        if self.current_event == NewMoonMode.FULL_MOON_VEGETARIAN:
            await self.do_full_moon_vegetarian_action(interface)
            return

        if self.current_event == NewMoonMode.SOMNAMBULISM:
            await self.do_somnambulism_action(interface, kwargs.get("target"))
            return

        if self.current_event == NewMoonMode.PUNISHMENT:
            await self.do_punishment_action(interface, kwargs.get("author"), kwargs.get("target"))
            return

    async def do_heads_or_tails_action(self, interface, coin_toss_value):
        if coin_toss_value != 0:
            coin_value_str = text_templates.get_word_in_language("coin_head")
        else:
            coin_value_str = text_templates.get_word_in_language("coin_tail")

        await self.send_result_text(interface, GAMEPLAY_CHANNEL, coin_value_str=coin_value_str)

    async def do_full_moon_vegetarian_action(self, interface):
        await self.send_result_text(interface, WEREWOLF_CHANNEL)

    async def do_punishment_action(self, interface, author, target):
        if not (author and target):
            return

        await self.send_result_text(interface, GAMEPLAY_CHANNEL, author=author, target=target)
        await self.send_result_text(interface, CEMETERY_CHANNEL, author=author, target=target)

    async def do_somnambulism_action(self, interface, target):
        if target is None:
            return

        await self.send_result_text(interface, GAMEPLAY_CHANNEL, target_role=target.get_role())
