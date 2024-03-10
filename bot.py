import sys

import discord
from commands import command, admin
from game import *
import config
import interface


# ============ Local functions ============


async def init_setup(init_game_list=False):
    """ Log ready message, check server roles/channels setup """
    startup_msg = "=========================BOT STARTUP========================="
    print(startup_msg)
    for guild in client.guilds:
        print("Connected to server: ", guild.name, " ServerID: ", guild.id, " Game Category: ", config.GAME_CATEGORY)
        if init_game_list is False:
            await admin.create_game_category(guild, client.user)
        # game_list.add_game(guild.id,Game(guild, interface.ConsoleInterface(guild)))
        game_list.add_game(guild.id, Game(guild, interface.DiscordInterface(guild, client)))

        await admin.send_text_to_channel(guild, startup_msg, config.LOBBY_CHANNEL)
        await admin.send_text_to_channel(guild, startup_msg, config.GAMEPLAY_CHANNEL)


async def process_message(discord_client, message):
    if message.content.strip().startswith(config.BOT_PREFIX):
        game = game_list.get_game(message.guild.id)
        if game is None:
            # Init game_list
            await init_setup(True)
            game = game_list.get_game(message.guild.id)

        await command.parse_command(discord_client, game, message)


def verify_ok(_):
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
intents = discord.Intents.all()  # Recent change in discord need set this to all()
intents.members = True
client = discord.Client(intents=intents)
game_list = GameList()


@client.event
async def on_ready():
    await init_setup()
    print("The bot is ready")

    # Uncomment to run test
    # server_id = config.DISCORD_TESTING_SERVER_ID  # Running test on Nhim's server
    # server_id = config.DISCORD_DEPLOY_SERVER_ID  # Running test on DNH ma sói bot's server
    # await test_bot(game_list.get_game(server_id), client.get_guild(server_id))


@client.event
async def on_message(message):
    if verify_ok(message):
        await process_message(client, message)  # loop through all commands and do action on first command that match


if __name__ == '__main__':
    if not config.DISCORD_TOKEN:
        print("Use must setup DISCORD_TOKEN in .env file")
        sys.exit(1)
    # keep_alive() # Uncomment to keep the bot alive
    client.run(config.DISCORD_TOKEN)
