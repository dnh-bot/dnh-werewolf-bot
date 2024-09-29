import utils

categories_info = utils.common.read_json_file("json/categories_config.json")
DEFAULT_CONFIG = categories_info.get("[default]")


class CategoryConfig(object):
    def __init__(self, category_name="[default]"):
        self.category_name = category_name
        self._config = categories_info.get(self.category_name, DEFAULT_CONFIG)
        # self.leaderboard_channel = category_config.get("LEADERBOARD_CHANNEL", "🏆leaderboard")
        # self.lobby_channel = category_config.get("LOBBY_CHANNEL", "🏠lobby")
        # self.gameplay_channel = category_config.get("GAMEPLAY_CHANNEL", "🎯gameplay")
        # self.werewolf_channel = category_config.get("WEREWOLF_CHANNEL", "🐺werewolf")
        # self.cemetery_channel = category_config.get("CEMETERY_CHANNEL", "💀cemetery")
        # self.couple_channel = category_config.get("COUPLE_CHANNEL", "💘couple")
        # self.personal_channel_prefix = category_config.get("PERSONAL_CHANNEL_PREFIX", "personal")

    def __getattr__(self, attr):
        attr_ = attr.upper()
        if attr_ in self._config:
            return self._config[attr_]
        elif attr_ in DEFAULT_CONFIG:
            return DEFAULT_CONFIG[attr_]
        return super().__getattribute__(attr)
