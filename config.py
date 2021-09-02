import os
from dotenv import load_dotenv
load_dotenv()
# ============ Configurations ===========
# DISCORD_TOKEN in .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_TESTING_SERVER_ID = int(os.getenv('DISCORD_TESTING_SERVER_ID')) # Testing server ID
DISCORD_DEPLOY_SERVER_ID = int(os.getenv('DISCORD_DEPLOY_SERVER_ID')) # Deploy server ID
DISCORD_TESTING_USER1_ID = int(os.getenv('DISCORD_TESTING_USER1_ID')) # Testing user1 ID
BOT_PREFIX = '!'