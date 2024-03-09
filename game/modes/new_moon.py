import random

from config import TEXT_LANGUAGE
import utils

new_moon_event_dict = utils.common.read_json_file("json/new_moon_events_info.json")


class NewMoonMode:
    NO_EVENT = "no_event"
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

    def do_coin_toss(self):
        return random.randint(0, 1)
