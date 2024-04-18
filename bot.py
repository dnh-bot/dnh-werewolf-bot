import sys

import discord
from discord.ext import commands as discord_commands
from commands import command, admin
from commands.command import BAN_FILE, BAN_DICT
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

        await command.process_command(discord_client, game, message)


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
client = discord_commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents)
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
        await client.process_commands(message)
        await process_message(client, message)  # loop through all commands and do action on first command that match


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        # await ctx.reply("That command wasn't found! Sorry :(")
        pass
    elif isinstance(error, discord.ext.commands.errors.MemberNotFound):
        await ctx.reply("You must mention a person!")


@discord_commands.command(name="ban")
async def do_ban(ctx, user: discord.Member, ban_duration='', *, ban_reason=text_templates.get_word_in_language("ban_no_reason")):
    try:
        ban_duration = command.timeparse(ban_duration) if ban_duration else 0
        if ban_duration == 0:
            ban_duration = command.timeparse("1000y")
        BAN_DICT[str(user.id)] = {
            "end_time": time.time() + ban_duration,
            "reason": ban_reason
        }
        utils.common.write_json_file(BAN_FILE, BAN_DICT)

        game = game_list.get_game(ctx.guild.id)
        if not game.is_started():
            await game.remove_player(user.id)

        await ctx.reply(text_templates.generate_text("ban_command_reply_text", user=user.mention, duration=command.time_string(ban_duration), reason=ban_reason))
    except ValueError:
        await ctx.reply("Must enter a valid ban duration.")
    except Exception as e:
        print("Error", e)
        await ctx.reply("Invalid usage. Must mention player to be banned")


@discord_commands.command(name="unban")
async def do_unban(ctx, user: discord.Member):
    try:
        if str(user.id) in BAN_DICT:
            del BAN_DICT[str(user.id)]
            utils.common.write_json_file(BAN_FILE, BAN_DICT)
            await ctx.reply(text_templates.generate_text("unban_command_reply_text", user=user.mention))
        else:
            await ctx.reply(text_templates.generate_text("unban_command_reply_not_banned_text"))
    except Exception as e:
        print("Error", e)
        await ctx.reply("Invalid usage. Must mention player to be unbanned")


# Commands
client.add_command(do_ban)
client.add_command(do_unban)

if __name__ == '__main__':
    if not config.DISCORD_TOKEN:
        print("Use must setup DISCORD_TOKEN in .env file")
        sys.exit(1)
    # keep_alive() # Uncomment to keep the bot alive
    client.run(config.DISCORD_TOKEN)
