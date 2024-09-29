from game.modes.new_moon.events.base import NewMoonEvent


class Punishment(NewMoonEvent):
    KEY = "punishment"

    @classmethod
    async def on_day_start(cls, interface, **kwargs):
        alive_players_embed_data = kwargs.get("alive_players_embed_data")
        if alive_players_embed_data:
            await interface.send_embed_to_channel(alive_players_embed_data, interface.config.CEMETERY_CHANNEL)
            await cls.send_announcement_text(interface, interface.config.CEMETERY_CHANNEL)

    @classmethod
    async def do_action(cls, interface, **kwargs):
        author_id = kwargs.get("author")
        target_id = kwargs.get("target")
        if author_id is None or target_id is None:
            return

        await cls.send_result_text(interface, interface.config.GAMEPLAY_CHANNEL, author=author_id, target=target_id)
        return cls.get_result_text(author=author_id, target=target_id)
