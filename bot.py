import discord
from commands import command
from game import *
import config
import interface

if not config.DISCORD_TOKEN:
    print("Use must setup DISCORD_TOKEN in .env file")
    exit(1)
# ============ Local functions ============


async def process_message(message):
    if message.content.strip().startswith(config.BOT_PREFIX):
        game = game_list.get_game(message.guild.id)
        await command.parse_command(game, message)


def verify_ok(user):
    # TODO: Check valid user in valid channel
    return True

# ============ Test Discord server =======
async def test_bot(game, guild):
    print("------------ Bot testing ------------")
    print(guild.name)
    # Test admin/player commands
    # await command.test_commands(guild)
    # Test game commands
    game.test_game()

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
        # game_list.add_game(guild.id,Game(guild, interface.ConsoleInterface(guild)))
        game_list.add_game(guild.id,Game(guild, interface.DiscordInterface(guild)))

    ''' Uncomment to run test '''
    await test_bot(game_list.get_game(config.DISCORD_TESTING_SERVER_ID), client.get_guild(config.DISCORD_TESTING_SERVER_ID)) #Running test on Nhim's server
    # await test_bot(game_list.get_game(config.DISCORD_DEPLOY_SERVER_ID), client.get_guild(config.DISCORD_DEPLOY_SERVER_ID)) #Running test on DNH ma sói bot's server



@client.event
async def on_message(message):
    # Check valid author
    if verify_ok(message.author):
        await process_message(message)  # loop through all commands and do action on first command that match


client.run(config.DISCORD_TOKEN)
