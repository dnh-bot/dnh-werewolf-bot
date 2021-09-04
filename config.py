import os
from dotenv import load_dotenv
load_dotenv()
# ============ Configurations ===========
# DISCORD_TOKEN in .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_TESTING_SERVER_ID = int(os.getenv('DISCORD_TESTING_SERVER_ID'))  # Testing server ID
DISCORD_DEPLOY_SERVER_ID = int(os.getenv('DISCORD_DEPLOY_SERVER_ID'))  # Deploy server ID
DISCORD_TESTING_USER1_ID = int(os.getenv('DISCORD_TESTING_USER1_ID'))  # Testing user1 ID
DISCORD_TESTING_USER2_ID = int(os.getenv('DISCORD_TESTING_USER2_ID'))  # Testing user1 ID

BOT_PREFIX = '!'

# each !next cmd have at least 15 seconds apart
NEXT_CMD_DELAY = 15

GAME_CATEGORY = "GAME"
LOBBY_CHANNEL = "lobby"
GAMEPLAY_CHANNEL = "gameplay"
WEREWOLF_CHANNEL = "werewolf"
