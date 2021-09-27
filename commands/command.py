from commands import admin, player
import config
from game import text_template, roles

import discord
import asyncio

ALL_COMMANDS = (
    "join", "leave", "start", "next", "stop", "status",
    "vote", "kill", "guard", "seer", "reborn",
    "timer", "timerstart", "timerstop"
)

# TODO: generate content of command embed_data
# e.g: Select a player to vote/kill/... by using command ...\nFor example: ...


def generate_usage_text_list(cmd, **kwargs):
    if cmd in ("vote", "kill", "guard", "seer", "reborn"):
        player_id = kwargs.get("player_id", "player_id")
        return [f"`{config.BOT_PREFIX}{cmd} {player_id}`", f"`{config.BOT_PREFIX}{cmd} @user`"]
    elif cmd == "timer":
        """Usage: 
        `!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
        """
        dayphase = kwargs.get("dayphase", "dayphase")
        nightphase = kwargs.get("nightphase", "nightphase")
        alertperiod = kwargs.get("alertperiod", "alertperiod")
        return [f"`{config.BOT_PREFIX}{cmd} {dayphase} {nightphase} {alertperiod}`"]
    else:
        return [f"`{config.BOT_PREFIX}{cmd}`"]


def generate_help_command_text(command=None):
    # TODO: read info from command_info.json file
    help_embed_data = {
        "title": "Werewolf Bot Help",
        "description": f"Full command list. You can get more information on a command using `{config.BOT_PREFIX}help cmd <name of command>`",
        "content": []
    }
    command = command.lower() if isinstance(command, str) else command
    if command is None:
        help_embed_data["color"] = (255, 255, 255)
        help_embed_data["content"] = [("All commands", [" | ".join(f"`{cmd}`" for cmd in ALL_COMMANDS)])]

    elif command in ALL_COMMANDS:
        help_embed_data["color"] = (23, 161, 104)
        help_embed_data["title"] += f" for command `{command}`"

        usage_str = ["- " + usage_text for usage_text in generate_usage_text_list(command)]
        help_embed_data["content"] = [("Usage", usage_str)]
        if command == "timer":
            help_embed_data["description"] = "Set the current timer."
        elif command == "timerstart":
            help_embed_data["description"] = "Start the current timer."
        elif command == "timerstop":
            help_embed_data["description"] = "Stop the current timer."

        elif command == "join":
            help_embed_data["description"] = "Join a game."
        elif command == "leave":
            help_embed_data["description"] = "Leave a game."
        elif command == "start":
            help_embed_data["description"] = "Start a game."
        elif command == "next":
            help_embed_data["description"] = "Jump to next phase."
        elif command == "stop":
            help_embed_data["description"] = "Stop a game."
        elif command == "status":
            # TODO: Show status of current phase.
            help_embed_data["description"] = "Show voting status of current daytime."

        else:
            if command == "vote":
                help_embed_data["description"] = f"A command for everyone to {command} an user."
            elif command == "kill":
                help_embed_data["description"] = f"A command for role Werewolf to {command} an user."
            elif command == "guard":
                help_embed_data["description"] = f"A command for role Guard to {command} an user."
            elif command == "seer":
                help_embed_data["description"] = f"A command for role Seer to {command} an user."
            elif command == "reborn":
                help_embed_data["description"] = f"A command for role Witch to {command} an user."

            help_embed_data["content"].append(
                ("Example", ["- " + usage_text for usage_text in generate_usage_text_list(command, player_id=2)])
            )
    else:
        help_embed_data["color"] = (220, 78, 78)
        help_embed_data["title"] = f"Invalid help for command `{command}`"
        help_embed_data["description"] = "A command with this name doesn't exist"

    return help_embed_data


def generate_help_role_text(role=None):
    help_embed_data = {
        "title": "Werewolf Bot Help",
        "description": f"Full role list. You can get more information on a role using `{config.BOT_PREFIX}help role <name of role>`",
        "content": []
    }
    all_roles_name = [a_role.__name__ for a_role in roles.get_all_roles()]
    role = role.capitalize() if isinstance(role, str) else role
    if role is None:
        help_embed_data["color"] = (255, 255, 255)
        for a_role in roles.get_all_roles():
            help_embed_data["content"].append((a_role.__name__, [a_role.get_character_description()]))

    elif role in all_roles_name:
        a_role = roles.get_role_type(role)
        help_embed_data["color"] = (52, 152, 219)
        help_embed_data["title"] += f" for role `{role}`"
        help_embed_data["description"] = a_role.get_character_description()
        get_usage_text = lambda cmd: " hoặc ".join(generate_usage_text_list(cmd))
        help_embed_data["content"] = [
            ("Ban ngày", [f"Được quyền chọn 1 người nào đó trong làng sẽ bị chém trong buổi hôm đó. Sử dụng command {get_usage_text('vote')}."]),
            (
                "Ban đêm", [
                    f"Được quyền chọn 1 người nào đó sẽ bị ăn thịt trong đêm đó. Sử dụng command {get_usage_text('kill')}." if role in ("Werewolf", "Superwolf") else
                    f"Soi một người có phải là sói hay không. Sử dụng command {get_usage_text('seer')}." if role == "Seer" else
                    f"Bảo vệ một người trong đêm đó. Sử dụng command {get_usage_text('guard')}." if role == "Guard" else
                    f"Hồi sinh một người đã chết. Sử dụng command {get_usage_text('reborn')}." if role == "Witch" else
                    "Chỉ việc đi ngủ thôi :joy:"
                ]
            ),
        ]
    else:
        help_embed_data["color"] = (220, 78, 78)
        help_embed_data["title"] = f"Invalid help for role `{role}`"
        help_embed_data["description"] = "A role with this name doesn't exist"

    return help_embed_data


def generate_help_text(*args):
    if len(args) == 0:
        help_embed_data = {
            "color": (255, 255, 255),
            "title": "Werewolf Bot Help",
            "description": "Full list of things. You can get more information on " +\
                           f"a command using `{config.BOT_PREFIX}help cmd <name of command>` or " +\
                           f"a role using `{config.BOT_PREFIX}help role <name of role>`",
            "content": [
                ("All commands", [" | ".join(f"`{cmd}`" for cmd in ALL_COMMANDS)]),
                ("All roles", [" | ".join(f"`{a_role.__name__}`" for a_role in roles.get_all_roles())])
            ]
        }
    elif args[0] == "role":
        help_embed_data = generate_help_role_text(None if len(args) == 1 else args[1])
    elif args[0] == "cmd":
        help_embed_data = generate_help_command_text(None if len(args) == 1 else args[1])
    else:
        help_embed_data = {
            "color": (220, 78, 78),
            "title": "Invalid help argument",
            "description": f"Argument with name `{args[0]}` doesn't exist. Please type `{config.BOT_PREFIX}help`.",
            "content": []
        }

    return help_embed_data


async def parse_command(client, game, message):
    message_parts = message.content.strip()[len(config.BOT_PREFIX):].split(" ")
    cmd, parameters = message_parts[0], message_parts[1:]
    # Game commands only valid under GAME CATEGORY:
    if admin.is_valid_category(message):
        if cmd == "help":
            await admin.send_embed_to_channel(
                message.guild, generate_help_text(*parameters), message.channel.name, False
            )

        elif cmd == "join":
            await player.do_join(game, message, force=False)
        elif cmd == "leave":
            await player.do_leave(game, message, force=False)
        elif cmd == "start":
            await player.do_start(game, message, force=False)
        elif cmd == "next":  # Next phase
            await player.do_next(game, message, force=False)
        elif cmd == "stop":
            await player.do_stop(game, message, force=False)

        elif cmd in ("vote", "kill", "guard", "seer", "reborn"):
            is_valid_channel = \
                (cmd == "vote" and message.channel.name == config.GAMEPLAY_CHANNEL) or\
                (cmd == "kill" and message.channel.name == config.WEREWOLF_CHANNEL) or\
                (cmd in ("guard", "seer", "reborn") and message.channel.name.strip().startswith("personal"))

            if is_valid_channel:
                author = message.author
                is_valid_command = False
                if len(parameters) == 1:
                    if len(message.raw_mentions) == 1:
                        is_valid_command = True
                        msg = await game.do_player_action(cmd, author.id, message.raw_mentions[0])
                        await message.reply(msg)

                    elif parameters[0].isdigit():
                        target_index = int(parameters[0]) - 1
                        if cmd == "reborn":
                            id_players = game.get_dead_players()
                        else:
                            id_players = game.get_alive_players()
                        if 0 <= target_index < len(id_players):
                            is_valid_command = True
                            target_user = id_players[target_index]
                            msg = await game.do_player_action(cmd, author.id, target_user.player_id)
                            await message.reply(msg)

                    if not is_valid_command:
                        await message.reply(text_template.generate_invalid_command_text(cmd))

                else:
                    await message.reply(text_template.generate_not_vote_1_player_text())
            else:
                if cmd == "vote":
                    real_channel = f"#{config.GAMEPLAY_CHANNEL}"
                elif cmd == "kill":
                    real_channel = f"#{config.WEREWOLF_CHANNEL}"
                else:
                    real_channel = "your personal channel"

                await admin.send_text_to_channel(
                    message.guild, text_template.generate_invalid_channel_text(real_channel), message.channel.name
                )

        elif cmd == "status":
            await player.do_generate_vote_status_table(message.channel, game.get_vote_status())

        elif cmd == "timer":
            """ Usage: 
                `!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
            """
            if len(parameters) < 3:
                timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
                await message.reply(
                    "Use default settings: " +
                    f"dayphase={config.DAYTIME}s, nightphase={config.NIGHTTIME}s, alertperiod={config.ALERT_PERIOD}s"
                )
            else:
                timer_phase = list(map(int, parameters))
                await message.reply(
                    "New settings: " +
                    f"dayphase={timer_phase[0]}s, nightphase={timer_phase[1]}s, alertperiod={timer_phase[2]}s"
                )
            game.set_timer_phase(timer_phase)

        elif cmd == "timerstart":
            game.timer_stopped = False
            await message.reply(text_template.generate_timer_start_text())
        elif cmd == "timerstop":
            game.timer_stopped = True
            await message.reply(text_template.generate_timer_stop_text())

        elif cmd.startswith('f'):
            if admin.is_admin(message.author):
                if cmd == "fjoin":
                    await admin.create_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL, is_public=False)
                    await player.do_join(game, message, force=True)
                elif cmd == "fleave":
                    await player.do_leave(game, message, force=True)
                elif cmd == "fstart":
                    await player.do_start(game, message, force=True)
                elif cmd == "fnext":  # Next phase
                    await player.do_next(game, message, force=True)
                elif cmd == "fstop":
                    await player.do_stop(game, message, force=True)
                elif cmd == "fclean":  # Delete all private channels under config.GAME_CATEGORY
                    try:
                        await admin.delete_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL)
                        await admin.delete_channel(message.guild, client.user, config.WEREWOLF_CHANNEL)
                        await admin.delete_channel(message.guild, client.user, config.CEMETERY_CHANNEL)
                        await admin.delete_all_personal_channel(message.guild)
                        await admin.create_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL, is_public=False)
                    except Exception as e:
                        print(e)
                elif cmd == "fdebug":
                    # print(asyncio.all_tasks())
                    exec(" ".join(parameters))
            else:
                await message.reply("You do not have Admin role.")

    # Admin/Bot commands - User should not directly use these commands
    if cmd.startswith('f'):
        if admin.is_admin(message.author):
            if cmd == "fcreate":  # Create game channels
                if len(message.mentions) == 1:
                    user = message.mentions[0]
                    if user.id == client.user.id:
                        await admin.create_category(message.guild, client.user, config.GAME_CATEGORY)
                        await admin.create_channel(message.guild, client.user, config.LOBBY_CHANNEL, is_public=True)
                        await admin.create_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL, is_public=False)
                else:
                    await message.reply("Missing @bot_name")
            elif cmd == "fdelete":  # Delete all channels and category under config.GAME_CATEGORY
                if len(message.mentions) == 1:
                    user = message.mentions[0]
                    try:
                        if user.id == client.user.id:
                            await admin.delete_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL)
                            await admin.delete_channel(message.guild, client.user, config.WEREWOLF_CHANNEL)
                            await admin.delete_channel(message.guild, client.user, config.CEMETERY_CHANNEL)
                            await admin.delete_all_personal_channel(message.guild)
                            await admin.delete_channel(message.guild, client.user, config.LOBBY_CHANNEL)
                            await admin.delete_category(message.guild, client.user)
                    except Exception as e:
                        print(e)
                else:
                    await message.reply("Missing @bot_name")
        else:  # No need to reply because there are many bots
            pass


async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
