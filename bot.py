from game.game import *

import discord
import os
from commands import command
from dotenv import load_dotenv

load_dotenv()
# ============ Configurations ===========
# DISCORD_TOKEN in .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = '!'

if not DISCORD_TOKEN:
    print("Use must setup DISCORD_TOKEN in .env file")
    exit(1)
# ============ Local functions ============


async def process_message(client, message):
    if message.content.strip().startswith(BOT_PREFIX):
        guild_game = game_list.get_game(message.guild.id)
        await command.parse_command(guild_game, client, message)


def verify_ok(user):
    # TODO: Check valid user in valid channel
    return True

# ============ Test Discord server =======
async def test_bot(guild_game, client):
    print("------------ Bot testing ------------")
    print(guild_game.name)
    # Test admin commands
    await command.test_commands(guild_game, client)
    # TODO: Test game commands
    pass
    print("------------ End bot testing ------------")

# ============ Discord server ============
# We need to enable intents to access guild.members list 
# details: https://discordpy.readthedocs.io/en/latest/intents.html#member-intent
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
game_list = GameList()

@client.event
async def on_ready():
    ''' Log ready message, check server roles/channels setup '''
    print("=========================BOT STARTUP=========================")
    for guild in client.guilds:
        print("Connected to server: ", guild.name, " ServerID: ", guild.id)
        game_list.add_game(guild.id,Game(guild.id))

    await test_bot(client.get_guild(881367187611349012), client) #Running test on Nhim's server
    # await test_bot(client.get_guild(881130452377825280), client) #Running test on DNH ma sói bot's server



@client.event
async def on_message(message):
    # Check valid author
    if verify_ok(message.author):
        await process_message(client, message)  # loop through all commands and do action on first command that match


client.run(DISCORD_TOKEN)
