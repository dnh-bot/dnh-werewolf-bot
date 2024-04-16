# import asyncio   # Do not remove this. This for debug command
import re
from datetime import *
import subprocess
import os
import time

import discord
from dateutil import parser, tz

from commands import admin, player
import commands
import config
from game import text_template, modes
import text_templates
import utils


def parse_time_str(time_str):
    args_matches = re.findall(r"^([+-])*(\d{1,2}|\d{1,2}:?\d{2})$", time_str)
    if len(args_matches):
        args_matches = args_matches[0]
        args_tz_sign = "+" if args_matches[0].count("-") % 2 == 0 else "-"
        args_tz_parts = args_matches[1].split(":")
        if len(args_tz_parts) == 2:  # \d+:\d+
            return args_tz_sign, args_tz_parts[0], args_tz_parts[1]
        if len(args_tz_parts[0]) <= 2:  # \d | \d\d
            return args_tz_sign, args_tz_parts[0], 0
        if len(args_tz_parts[0]) <= 4:  # (\d)(\d\d) | (\d\d)(\d\d)
            return args_tz_sign, args_tz_parts[0][:-2], args_tz_parts[0][-2:]

    return None


UNITS = dict(zip("s m h d w y".split(), (1, 60, 60 * 60, 24 * 60 * 60, 7 * 24 * 60 * 60, 365 * 24 * 60 * 60)))


def timeparse(string):
    return int(''.join(c for c in string if c.isnumeric())) * UNITS.get(string[-1], 1)


def time_string(sec):
    for u in "y w d h m s".split():
        if sec > UNITS[u]:
            return f'{int(sec)//UNITS[u]}{u}'
    return f'{sec}s'


def check_set_timer_input(input_string):
    try:
        return [timeparse(phase) for phase in input_string]
    except:  # pylint: disable=bare-except
        return None
  
async def get_member_by_id_string(message, user_id):
    # Get exactly the id without the <@> syntax
    user_id = user_id[2:-1]
    guild = message.guild
    try:
        if guild is not None:
            member = discord.utils.get(guild.members, id=int(user_id))
            if member is not None:
                return member
    except:
        return

async def process_command(client, game, message):
    message_parts = message.content.strip()[len(config.BOT_PREFIX):].split()
    cmd, parameters = message_parts[0], message_parts[1:]
    
    # Mentions can be anywhere in the parameters list for other command usage 
    for i in range(len(parameters)):
        if parameters[i].startswith("<@") and parameters[i].endswith(">"):
            parameters[i] = await get_member_by_id_string(message, parameters[i])

    try:
        await parse_command(client, game, message, cmd, parameters)
        # TODO: reply message here
    except Exception as e:
        print(f"Error in process_command with cmd={cmd}:", e)


async def parse_command(client, game, message, cmd, parameters):
    # TODO: Return True/False (if it's a valid and authorized command name) and message to be replied.
    # FIXME:
    # pylint: disable=too-many-nested-blocks, too-many-branches
    if not admin.is_valid_category(message):
        return

    # Game commands only valid under GAME CATEGORY
    if cmd.startswith(config.ADMIN_CMD_PREFIX):
        # Admin/Bot commands - User should not directly use these commands
        await do_admin_cmd(client, game, message, cmd, parameters)
    elif cmd == "help":
        await admin.send_embed_to_channel(
            message.guild, text_template.generate_help_embed(*parameters), message.channel.name, False
        )
    elif cmd == "version":
        tag = subprocess.check_output(["git", "describe", "--tags"]).decode('utf-8')  # git describe --tags
        name = os.getenv("BOT_NAME")
        await message.reply(f"{name}-{tag}".rstrip('\n'))  # prevent bug of name's or tag's type
    else:
        await do_game_cmd(game, message, cmd, parameters)


async def do_game_cmd(game, message, cmd, parameters, force=False):
    # FIXME
    # pylint: disable=too-many-branches
    if not commands.is_command_in_valid_channel(cmd, message.channel.name):
        real_channel = commands.get_command_valid_channel_name(cmd)
        await message.reply(text_templates.generate_text("invalid_channel_text", channel=real_channel))
        return

    if cmd == "join":
        if not force:
            ban_remain = BAN_DICT.get(str(message.author.id), {"end_time": 0})["end_time"] - time.time()
            ban_reason = BAN_DICT.get(str(message.author.id), {"reason": text_templates.get_word_in_language("ban_no_reason")})["reason"]
            if ban_remain > 0:
                await message.reply(text_templates.generate_text("join_while_ban_reply_text", duration=time_string(ban_remain), reason=ban_reason))
                return
            # Remove from list if ban time expired
            if str(message.author.id) in BAN_DICT:
                del BAN_DICT[str(message.author.id)]
                utils.common.write_json_file(BAN_FILE, BAN_DICT)
        await player.do_join(game, message, force=force)

    elif cmd in ("watch", "unwatch", "leave", "start", "next", "stopgame"):
        command_function = getattr(player, f"do_{cmd}")
        await command_function(game, message, force=force)

    elif cmd == "rematch":
        if message.channel.name != config.LOBBY_CHANNEL:  # Any player can request rematch, so only allow in Lobby
            await message.reply(text_templates.generate_text("invalid_channel_text", channel=f"#{config.LOBBY_CHANNEL}"))
            return
        await player.do_rematch(game, message)

    elif cmd in ("vote", "punish", "kill", "guard", "seer", "hunter", "reborn", "curse", "zombie", "ship", "auto"):
        try:
            await player.do_character_cmd(game, message, cmd, parameters)
        except Exception as e:
            print(f"Error in do_character_cmd with cmd={cmd}:", e)

    elif cmd == "selfcheck":
        if not game.is_started():
            await message.reply(text_templates.generate_text("game_not_started_text"))
            return

        msg = await game.self_check_channel()
        await message.reply(msg)

    elif cmd == "status":
        await game.show_status(message.author, message.channel.name)

    elif cmd == "timer":
        # Usage:`!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
        if len(parameters) < 3:
            timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
            settings_name = "default"
        else:
            timer_phase = check_set_timer_input(parameters)
            settings_name = "new"
            if not timer_phase:
                await message.reply("Invalid input for timer")
                return
            # Check if any timer phase is too short (<= 30 seconds):
            if any(x <= 30 for x in timer_phase):
                await message.reply("Config must greater than 30s")
                return

        await message.reply(
            text_templates.generate_text(
                "timer_settings_text",
                settings_name=text_templates.get_word_in_language(settings_name),
                day_phase=timer_phase[0],
                night_phase=timer_phase[1],
                alert_period=timer_phase[2]
            )
        )
        game.set_timer_phase(timer_phase)

    elif cmd == "timerstart":
        game.timer_stopped = False
        await message.reply(text_templates.generate_text("timer_start_text"))
    elif cmd == "timerstop":
        game.timer_stopped = True
        await message.reply(text_templates.generate_text("timer_stop_text"))

    elif cmd == "setplaytime":
        parsed_data = parse_setplaytime_params(parameters)
        if parsed_data is None:
            await message.reply(text_template.generate_invalid_command_text(cmd))
        else:
            start_time_utc_time, end_time_utc_time, zone = parsed_data
            game.set_play_time(start_time_utc_time, end_time_utc_time, zone)
            await message.reply(text_template.generate_play_time_text(start_time_utc_time, end_time_utc_time, zone))

    elif cmd == "setroles":
        res = game.add_default_roles(parameters)
        await message.reply(res)
    elif cmd == "showmodes":
        game_modes = utils.common.read_json_file("json/game_config.json")
        await message.reply(modes.generate_modes_text(game_modes))
    elif cmd == "setmode":
        try:
            mode_id, status = parameters[0], parameters[1]
            res = game.set_mode(mode_id, status)
            await message.reply(res)
        except Exception as e:
            print(e)
            await message.reply('Invalid usage.')


def parse_setplaytime_params(parameters):
    # Usage: `!setplaytime 10:00 21:00 UTC+7` -> start_time = 10:00, end_time = 21:00, zone=UTC+7
    if len(parameters) < 2:
        return None

    zone = "UTC+7"
    if len(parameters) >= 3:
        zone = parameters[2]

    try:
        if zone:
            preprocessed_zone = re.sub(r"(?:GMT|UTC)([+-]\d+)", r"\1", zone)
            start_time = parser.parse(f"{parameters[0]} {preprocessed_zone}")
            end_time = parser.parse(f"{parameters[1]} {preprocessed_zone}")
        else:
            start_time = parser.parse(f"{parameters[0]}")
            end_time = parser.parse(f"{parameters[1]}")

    except parser.ParserError:
        return None

    start_time_utc = start_time.astimezone(tz.UTC)
    end_time_utc = end_time.astimezone(tz.UTC)
    return start_time_utc.time(), end_time_utc.time(), zone


async def do_admin_cmd(client, game, message, cmd, parameters):
    if not admin.is_admin(message.author):
        if admin.is_valid_category(message):
            await message.reply("You do not have Admin role.")
        return

    cmd_content = cmd[len(config.ADMIN_CMD_PREFIX):]

    if cmd_content == "create":
        await do_force_create(client, message)
    elif cmd_content == "delete":
        await do_force_delete(client, message)
    elif cmd_content == "clean":
        await do_force_clean(client, message)
    elif cmd_content == "debug":
        await do_force_debug()
    elif cmd_content == "ban":
        await do_ban(game, message, parameters)
    elif cmd_content == "unban":
        await do_unban(message, parameters)
    elif cmd_content in ("join", "leave", "start", "next", "stopgame"):
        await do_game_cmd(game, message, cmd_content, parameters, True)


async def do_force_clean(client, message):
    """Delete all private channels under config.GAME_CATEGORY"""
    await admin.clean_game_category(message.guild, client.user, False)


async def do_force_debug():
    # print(asyncio.all_tasks())
    # exec(" ".join(parameters))
    pass


async def do_force_create(client, message):
    """Create game channels"""
    if not message.mentions:
        await message.reply("Missing @bot_name")

    user = message.mentions[0]
    if user.id == client.user.id:
        await admin.create_game_category(message.guild, client.user)


async def do_force_delete(client, message):
    """Delete all channels and category under config.GAME_CATEGORY"""
    if not message.mentions:
        await message.reply("Missing @bot_name")

    user = message.mentions[0]
    if user.id == client.user.id:
        await admin.clean_game_category(message.guild, client.user, True)


BAN_FILE = "json/ban_list.json"
BAN_DICT = utils.common.read_json_file(BAN_FILE)


async def do_ban(game, message, params):
    if not isinstance(params[0], discord.Member):
        await message.reply("Invalid usage.")
        return

    user = params[0]
    ban_duration = timeparse(params[1]) if len(params) > 1 else 0
    ban_reason = ' '.join(params[2:]) if len(params) > 2 else text_templates.get_word_in_language("ban_no_reason")
    if ban_duration == 0:
        ban_duration = timeparse("1000y")
    BAN_DICT[str(user.id)] = {
        "end_time": time.time() + ban_duration,
        "reason": ban_reason
    }
    utils.common.write_json_file(BAN_FILE, BAN_DICT)
    if not game.is_started():
        await game.remove_player(user.id)
    await message.reply(text_templates.generate_text("ban_command_reply_text", user=user.mention, duration=time_string(ban_duration), reason=ban_reason))


async def do_unban(message, params):
    if not isinstance(params[0], discord.Member):
        await message.reply("Invalid usage.")
        return

    user = params[0]
    if str(user.id) in BAN_DICT:
        del BAN_DICT[str(user.id)]
        utils.common.write_json_file(BAN_FILE, BAN_DICT)
        await message.reply(text_templates.generate_text("unban_command_reply_text", user=user.mention))
    else:
        await message.reply(text_templates.generate_text("unban_command_reply_not_banned_text"))


async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
