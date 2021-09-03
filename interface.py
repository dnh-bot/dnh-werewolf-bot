import asyncio
import commands

class ConsoleInterface:
    def send_text_to_channel(self, msg, channel):
        print("{channel}: {msg}".format(channel=channel, msg=msg))

    def create_channel(self, channel):
        print("{channel} created!".format(channel=channel))


def run(f, *a, **kw):
    if asyncio.iscoroutinefunction(f):
        loop = asyncio.get_event_loop()
        r = loop.run_until_complete(f(*a, **kw))
        loop.close()
        return r
    else:
        return f(*a, **kw)

class DiscordInterface:
    def send_text_to_channel(self, msg, channel):
        return run(commands.admin.send_text_to_channel, msg, channel)

    def create_channel(self, channel)
        return run(commands.admin.create_channel, channel)



