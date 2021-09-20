import discord
from commands import command, admin
from game import *
import config
import interface

if not config.DISCORD_TOKEN:
    print("Use must setup DISCORD_TOKEN in .env file")
    exit(1)
# ============ Local functions ============


async def process_message(client, message):
    if message.content.strip().startswith(config.BOT_PREFIX):
        game = game_list.get_game(message.guild.id)
        await command.parse_command(client, game, message)


def verify_ok(message):
    return True


# ============ Test Discord server =======
async def test_bot(game, guild):
    print("\n\n\n=====================================")
    print("------------ Bot testing ------------")
    print(guild.name)
    # Test admin/player commands
    # await command.test_commands(guild)
    # Test game commands
    await game.test_game()
    # await game.test_game()  # Rerun second time

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
        await admin.create_category(guild, client.user, config.GAME_CATEGORY)  # Create GAME_CATEGORY if not existing
        await admin.create_channel(guild, client.user, config.LOBBY_CHANNEL, is_public=True)
        await admin.create_channel(guild, client.user, config.GAMEPLAY_CHANNEL, is_public=False)
        # game_list.add_game(guild.id,Game(guild, interface.ConsoleInterface(guild)))
        game_list.add_game(guild.id, Game(guild, interface.DiscordInterface(guild, client)))

    ''' Uncomment to run test '''
    server_id = config.DISCORD_TESTING_SERVER_ID  # Running test on Nhim's server
    # server_id = config.DISCORD_DEPLOY_SERVER_ID  # Running test on DNH ma sói bot's server
    # await test_bot(game_list.get_game(server_id), client.get_guild(server_id))


@client.event
async def on_message(message):
    if verify_ok(message):
        await process_message(client, message)  # loop through all commands and do action on first command that match


client.run(config.DISCORD_TOKEN)
