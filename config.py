import os
from dotenv import load_dotenv
load_dotenv()
# ============ Configurations ===========
# DISCORD_TOKEN in .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_TESTING_SERVER_ID = int(os.getenv('DISCORD_TESTING_SERVER_ID'))
DISCORD_DEPLOY_SERVER_ID = int(os.getenv('DISCORD_DEPLOY_SERVER_ID'))
DISCORD_TESTING_USER1_ID = int(os.getenv('DISCORD_TESTING_USER1_ID'))
DISCORD_TESTING_USER2_ID = int(os.getenv('DISCORD_TESTING_USER2_ID'))
DISCORD_TESTING_ADMIN1_ID = int(os.getenv('DISCORD_TESTING_ADMIN1_ID'))

DISCORD_TESTING_USERS_ID = list(map(int, os.getenv('DISCORD_TESTING_USERS_ID').split(',')))

BOT_PREFIX = '!'

''' Configurable value '''
# each !next cmd have at least 60 seconds apart
NEXT_CMD_DELAY = 60
VOTE_RATE = 0.5  # 50%
DAYTIME = 60    # 60s
NIGHTTIME = 30  # 30s
ALERT_PERIOD = 20  # 20s

''' Non-configurable value '''
GAME_CATEGORY = "GAME"
LOBBY_CHANNEL = "lobby"
GAMEPLAY_CHANNEL = "gameplay"
WEREWOLF_CHANNEL = "werewolf"
