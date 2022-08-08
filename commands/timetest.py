from datetime import *
from dateutil import parser, tz
import tzlocal

def date_range_to_string(start_time, end_time):

    if start_time == end_time:
        result = "cả ngày"
    else:
        result = f"từ {start_time} đến "
        if str(end_time) == "00:00":
            result += f"hết ngày"
        else:
            result += f"{end_time}{'' if start_time < end_time else ' ngày hôm sau'}"

    return result

def generate_play_time(start, end, zone):
    start_time_utc = parser.parse(f"{start} {zone}")
    end_time_utc = parser.parse(f"{end} {zone}")

    # Convert time zone
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(zone)
    start_time = start_time_utc.replace(tzinfo=to_zone).astimezone(from_zone)
    end_time = end_time_utc.replace(tzinfo=to_zone).astimezone(from_zone)

    msg = f"Bạn sẽ được chơi {date_range_to_string(start_time.time(), end_time.time())} (theo múi giờ {zone})"
    msg += f", hay {date_range_to_string(start, end)} (giờ UTC)."

    return msg

parameters = ("20:00", "22:30") 
zone = "UTC+8"

start_time = parser.parse(f"{parameters[0]} {zone}")
end_time = parser.parse(f"{parameters[1]} {zone}")

to_zone = tz.gettz("UTC")
start_time_utc = start_time.astimezone(to_zone)
end_time_utc = end_time.astimezone(to_zone)
print(start_time_utc.time())
print(start_time.time())

msg = generate_play_time(start_time_utc.time(), end_time_utc.time(), zone)
print(msg)
