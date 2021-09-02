import discord
from commands import command
from game.game import *
from config import *


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
async def test_bot(game, client, guild):
    print("------------ Bot testing ------------")
    print(guild.name)
    # Test admin commands
    await command.test_commands(client, guild)
    # Test game commands
    await command.send_text_to_channel(game, "Test sending message in public channel", "general")
    await command.send_text_to_channel(game, "Test sending message in private channel", "werewolf")
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
        game_list.add_game(guild.id,Game(guild))

    ''' Uncomment to run test '''
    # await test_bot(game_list.get_game(DISCORD_TESTING_SERVER_ID), client, client.get_guild(DISCORD_TESTING_SERVER_ID)) #Running test on Nhim's server
    # await test_bot(game_list.get_game(DISCORD_DEPLOY_SERVER_ID), client, client.get_guild(DISCORD_DEPLOY_SERVER_ID)) #Running test on DNH ma sói bot's server



@client.event
async def on_message(message):
    # Check valid author
    if verify_ok(message.author):
        await process_message(client, message)  # loop through all commands and do action on first command that match


client.run(DISCORD_TOKEN)
