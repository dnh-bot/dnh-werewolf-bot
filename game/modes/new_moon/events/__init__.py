import random

import utils
from game.modes.new_moon.events.no_event import NoEvent
from game.modes.new_moon.events.heads_or_tails import HeadsOrTails
from game.modes.new_moon.events.somnambulism import Somnambulism
from game.modes.new_moon.events.twin_flame import TwinFlame
from game.modes.new_moon.events.full_moon_vegetarian import FullMoonVegetarian
from game.modes.new_moon.events.punishment import Punishment

ALL_EVENTS = utils.common.read_json_file("json/new_moon_events_info.json")

EVENTS_LIST = [
    NoEvent,
    HeadsOrTails,
    TwinFlame,
    Somnambulism,
    FullMoonVegetarian,
    Punishment,
]


def generate_random_event():
    event_str = random.choices(*zip(*[
        (event_key, event["rate"])
        for event_key, event in ALL_EVENTS.items()
    ]))[0]
    return [e for e in EVENTS_LIST if e.KEY == event_str][0]
