# import asyncio   # Do not remove this. This for debug command
import re
from datetime import *
import subprocess
import os

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


async def parse_command(client, game, message):
    # FIXME:
    # pylint: disable=too-many-nested-blocks, too-many-branches
    message_parts = message.content.strip()[len(config.BOT_PREFIX):].split(" ")
    cmd, parameters = message_parts[0], message_parts[1:]

    if cmd.startswith('f'):
        # Admin/Bot commands - User should not directly use these commands
        await do_admin_cmd(client, game, message, cmd, parameters)
    elif admin.is_valid_category(message):
        # Game commands only valid under GAME CATEGORY

        if cmd == "help":
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
    if not commands.is_command_in_valid_channel(cmd, message.channel.name):
        real_channel = commands.get_command_valid_channel_name(cmd)
        await message.reply(text_templates.generate_text("invalid_channel_text", channel=real_channel))
        return

    if cmd in ("watch", "unwatch"):
        command_function = getattr(player, f"do_{cmd}")
        await command_function(game, message)

    elif cmd in ("join", "leave", "start", "next"):
        command_function = getattr(player, f"do_{cmd}")
        await command_function(game, message, force=force)

    elif cmd == "stopgame":
        await player.do_stop(game, message, force=force)

    elif cmd in ("vote", "kill", "guard", "seer", "hunt", "reborn", "curse", "zombie", "ship", "auto"):
        await player.do_character_cmd(game, message, cmd, parameters)

    elif cmd == "selfcheck":
        if not game.is_started():
            await message.reply(text_templates.generate_text("game_not_started_text"))
            return

        msg = await game.self_check_channel()
        await message.reply(msg)

    elif cmd == "status":
        do_status(game, message)

    elif cmd == "timer":
        # Usage:`!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
        if len(parameters) < 3:
            timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
            settings_name = "default"
        else:
            timer_phase = list(map(int, parameters[:3]))
            settings_name = "new"
            # Check if any timer phase is too short (<= 5 seconds):
            if any(x <= 5 for x in timer_phase):
                await message.reply("Config must greater than 5s")
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


def do_status(game, message):
    if game.is_ended():
        await admin.send_text_to_channel(
            message.guild, text_templates.generate_text("end_text"), message.channel.name
        )
        return

    status_description, remaining_time, vote_table, table_title, author_status = game.get_game_status(
        message.channel.name, message.author.id
    )
    print(
        status_description, remaining_time, vote_table,
        text_template.generate_vote_field(vote_table), table_title, author_status
    )
    embed_data = text_templates.generate_embed(
        "game_status_with_table_embed",
        [
            [text_template.generate_timer_remaining_text(remaining_time)],
            text_template.generate_vote_field(vote_table),
            [author_status]
        ],
        status_description=status_description,
        phase_str=text_templates.get_word_in_language(str(game.game_phase)),
        table_title=table_title
    )
    await admin.send_embed_to_channel(message.channel.guild, embed_data, message.channel.name)

    role_list = [game.get_role_list()]
    players_embed_data = text_template.generate_player_list_embed(
        game.get_all_players(), None, role_list, game.modes.get("reveal_role", False)
    )
    await admin.send_embed_to_channel(message.channel.guild, players_embed_data, message.channel.name)


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

    if cmd == "fcreate":
        await do_fcreate(client, message)
    elif cmd == "fdelete":
        await do_fdelete(client, message)
    elif cmd == "fclean":
        await do_fclean(client, message)
    elif cmd == "fdebug":
        await do_fdebug()
    elif cmd in ("fjoin", "fleave", "fstart", "fnext", "fstopgame"):
        await do_game_cmd(game, message, cmd[1:], parameters, True)


async def do_fclean(client, message):
    """Delete all private channels under config.GAME_CATEGORY"""
    await admin.clean_game_category(message.guild, client.user, False)


async def do_fdebug():
    # print(asyncio.all_tasks())
    # exec(" ".join(parameters))
    pass


async def do_fcreate(client, message):
    """Create game channels"""
    if not message.mentions:
        await message.reply("Missing @bot_name")

    user = message.mentions[0]
    if user.id == client.user.id:
        await admin.create_game_category(message.guild, client.user)


async def do_fdelete(client, message):
    """Delete all channels and category under config.GAME_CATEGORY"""
    if not message.mentions:
        await message.reply("Missing @bot_name")

    user = message.mentions[0]
    if user.id == client.user.id:
        await admin.clean_game_category(message.guild, client.user, True)


async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
