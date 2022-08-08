import re
from dateutil import parser, tz
from game.text_template import generate_play_time_text


def parse_play_time(start, end, zone=""):
    try:
        if zone:
            preprocessed_zone = re.sub(r"(?:GMT|UTC)([+-]\d+)", r"\1", zone)
            start_time = parser.parse(f"{start} {preprocessed_zone}")
            end_time = parser.parse(f"{end} {preprocessed_zone}")
        else:
            start_time = parser.parse(f"{start}")
            end_time = parser.parse(f"{end}")

        start_time_utc = start_time.astimezone(tz.UTC)
        end_time_utc = end_time.astimezone(tz.UTC)

        print(generate_play_time_text(start_time_utc.time(), end_time_utc.time(), zone))

    except parser.ParserError:
        start_time, end_time = None, None
        print("Invalid format")

    return start_time, end_time


parse_play_time("20:00", "00:00")
parse_play_time("20:00", "00:00", "+8")
parse_play_time("20:00", "00:00", "+08")
parse_play_time("20:00", "00:00", "UTC+8")
parse_play_time("20:00", "00:00", "UTC+8:00")
parse_play_time("20:00", "00:00", "UTC+08:00")
parse_play_time("20:00", "00:00", "UTC+0800")
