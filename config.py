import os
from dotenv import load_dotenv
load_dotenv()
# ============ Configurations ===========
# DISCORD_TOKEN in .env file
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_BOT_NAME = os.getenv("DISCORD_BOT_NAME")
DISCORD_TESTING_SERVER_ID = int(os.getenv("DISCORD_TESTING_SERVER_ID"))
DISCORD_DEPLOY_SERVER_ID = int(os.getenv("DISCORD_DEPLOY_SERVER_ID"))
DISCORD_TESTING_USER1_ID = int(os.getenv("DISCORD_TESTING_USER1_ID"))
DISCORD_TESTING_USER2_ID = int(os.getenv("DISCORD_TESTING_USER2_ID"))
DISCORD_TESTING_ADMIN1_ID = int(os.getenv("DISCORD_TESTING_ADMIN1_ID"))

DISCORD_TESTING_USERS_ID = list(map(int, os.getenv("DISCORD_TESTING_USERS_ID").split(",")))

PREFIX = os.getenv("BOT_PREFIX")
if PREFIX:
    BOT_PREFIX = PREFIX
else:
    BOT_PREFIX = "!"

""" Configurable value """
# each !next cmd have at least 60 seconds apart
NEXT_CMD_DELAY = 30
VOTE_RATE = 0.5     # 50%
DAYTIME = 240       # 60s
NIGHTTIME = 60      # 30s
ALERT_PERIOD = 30   # 20s

GUARD_PREVENT_SELF_PROTECTION = False  # Use True if do not want guard use skill on himself
SEER_CAN_KILL_FOX = True

""" Non-configurable value """
GAME_CATEGORY = os.getenv("GAME_CATEGORY") if os.getenv("GAME_CATEGORY") else "GAME"

LOBBY_CHANNEL = "lobby"
GAMEPLAY_CHANNEL = "gameplay"
WEREWOLF_CHANNEL = "werewolf"
CEMETERY_CHANNEL = "cemetery"
