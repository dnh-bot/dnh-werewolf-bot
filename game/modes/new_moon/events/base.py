import text_templates


class NewMoonEvent:
    KEY = ""

    @classmethod
    async def send_announcement_text(cls, interface, channel_name, **kwargs):
        await interface.send_action_text_to_channel(f"new_moon_{cls.KEY}_announcement_text", channel_name, **kwargs)

    @classmethod
    async def send_result_text(cls, interface, channel_name, **kwargs):
        await interface.send_action_text_to_channel(f"new_moon_{cls.KEY}_result_text", channel_name, **kwargs)

    @classmethod
    def get_result_text(cls, **kwargs):
        return text_templates.generate_text(f"new_moon_{cls.KEY}_result_text", **kwargs)

    @classmethod
    async def on_day_start(cls, interface, **kwargs):
        pass

    @classmethod
    async def on_day_end(cls, interface, **kwargs):
        pass

    @classmethod
    async def on_night_start(cls, interface, **kwargs):
        pass

    @classmethod
    async def on_night_end(cls, interface, **kwargs):
        pass

    @classmethod
    async def do_action(cls, interface, **kwargs):
        # Do event action. Return action result.
        pass
