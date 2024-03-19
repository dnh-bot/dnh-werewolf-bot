"""
This provides APIs for Player role
"""
import time
import math

import commands
import config
from game import text_template
import text_templates


def check_vote_valid(num_votes, num_players, task_name):
    if task_name == "start" and num_players < 4:
        return False, text_templates.generate_text("players_not_enough_text", task_name=task_name)

    if num_votes / num_players <= config.VOTE_RATE:
        return False, text_templates.generate_text("vote_rate_not_enough_text", task_name=task_name, votes_num=num_votes, players_num=num_players, min_votes_num=math.floor(num_players * config.VOTE_RATE) + 1)

    # Should never see it :D
    return True, text_templates.generate_text("vote_rate_enough_text", task_name=task_name)


async def do_join(game, message, force=False):
    """Join game"""
    if not game.is_started():
        if force:
            user_list = message.mentions
            if not user_list:
                await message.reply(text_template.generate_invalid_command_text(config.ADMIN_CMD_PREFIX + "join"))
        else:
            user_list = [message.author]

        for user in user_list:
            joined_players = await game.add_player(user.id, user.name if force else f"{user.name}-{user.discriminator}")
            if joined_players > 0:
                await message.channel.send(text_templates.generate_text("reply_join_text", user=user.display_name, joined_players=joined_players))
            else:
                await message.channel.send(text_templates.generate_text("already_in_game_text"))
    else:
        await message.reply(text_templates.generate_text("game_already_started_text"))


async def do_leave(game, message, force=False):
    """Leave game"""
    if not game.is_started():
        if force:
            user_list = message.mentions
            if not user_list:
                await message.reply(text_template.generate_invalid_command_text(config.ADMIN_CMD_PREFIX + "leave"))
        else:
            user_list = [message.author]

        for user in user_list:
            joined_players = await game.remove_player(user.id)
            if joined_players >= 0:
                await message.channel.send(text_templates.generate_text("reply_leave_text", user=user.display_name, joined_players=joined_players))
            else:
                await message.channel.send(text_templates.generate_text("not_in_game_text"))
    else:
        await message.reply(text_templates.generate_text("game_already_started_text"))


async def do_watch(game, message):
    """Watch game"""
    watched_players = await game.add_watcher(message.author.id)
    if watched_players > 0:
        await message.channel.send(text_templates.generate_text("reply_watch_text", user=message.author.display_name, watched_players=watched_players))
    elif watched_players == -1:
        await message.channel.send(text_templates.generate_text("already_watched_game_text"))
    elif watched_players == -2:
        await message.channel.send(
            text_templates.generate_text("already_in_game_text") + " " +
            text_templates.generate_text("reply_in_game_watch_text")
        )


async def do_unwatch(game, message):
    """Unwatch game"""
    watched_players = await game.remove_watcher(message.author.id)
    if watched_players >= 0:
        await message.channel.send(text_templates.generate_text("reply_unwatch_text", user=message.author.display_name, watched_players=watched_players))
    elif watched_players == -1:
        await message.channel.send(text_templates.generate_text("not_watched_game_text"))
    elif watched_players == -2:
        await message.channel.send(
            text_templates.generate_text("already_in_game_text") + " " +
            text_templates.generate_text("reply_in_game_unwatch_text")
        )


# Require at least 2 players to start the game
async def do_start(game, message, force=False):
    """Start game"""
    if not game.is_started():
        if force:
            await game.start()
            await message.channel.send(text_templates.generate_text("game_started_text"))
        else:
            if message.author.id not in game.players:
                await message.reply(text_templates.generate_text("not_in_game_text"))
            else:
                game.vote_start.add(message.author.id)
                valid, text = check_vote_valid(len(game.vote_start), len(game.players), "start")
                if valid:
                    await game.start()
                    await message.channel.send(text_templates.generate_text("game_started_text"))
                else:
                    await message.reply(text_templates.generate_text("vote_for_game_text", command="start", author=message.author.display_name, text=text))
    else:
        await message.reply(text_templates.generate_text("game_already_started_text"))


async def do_next(game, message, force=False):
    """Next phase"""
    if game.is_started():
        if force:
            await game.next_phase_cmd()
        else:
            if time.time() - game.get_last_nextcmd_time() > config.NEXT_CMD_DELAY:
                # User needs to wait for next phase
                if message.author.id not in game.players:
                    await message.reply(text_templates.generate_text("not_in_game_text"))
                else:
                    game.vote_next.add(message.author.id)
                    valid, text = check_vote_valid(len(game.vote_next), len(game.get_alive_players()), "next")
                    if valid:
                        await game.next_phase_cmd()
                    else:
                        await message.reply(text_templates.generate_text("vote_for_game_text", command="next", author=message.author.display_name, text=text))
            else:
                await message.reply(text_templates.generate_text("too_quick_text", wait_time=config.NEXT_CMD_DELAY - time.time() + game.get_last_nextcmd_time()))
    else:
        await message.reply(text_templates.generate_text("game_not_started_text"))


# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stopgame` to end the game
async def do_stopgame(game, message, force=False):
    """Stop game"""
    if game.is_started():
        if force:
            await message.channel.send(text_templates.generate_text("game_stop_text"))
            await game.stop()
        else:
            if message.author.id not in game.players:
                await message.reply(text_templates.generate_text("not_in_game_text"))
            else:
                game.vote_stop.add(message.author.id)
                valid, text = check_vote_valid(len(game.vote_stop), 1 if game.is_ended() else 2, "stop")
                if valid:
                    await message.reply(text_templates.generate_text("game_stop_text"))
                    await game.stop()
                else:
                    await message.reply(text_templates.generate_text("vote_for_game_text", command="stop", author=message.author.display_name, text=text))
    else:
        await message.reply(text_templates.generate_text("game_not_started_text"))


async def do_character_cmd(game, message, cmd, parameters):
    if not game.is_started():
        # prevent user uses command before game starts
        await message.reply(text_templates.generate_text("game_not_started_text"))
        return

    if not game.is_in_play_time():
        await message.reply(text_templates.generate_text("game_not_playing_text"))
        return

    author = message.author
    required_param_number = len(commands.get_command_required_params(cmd))

    if cmd == "auto":
        msg = await game.do_player_action(cmd, author.id, *parameters)
        await message.reply(msg)

    elif len(message.raw_mentions) == required_param_number:
        msg = await game.do_player_action(cmd, author.id, *message.raw_mentions)
        await message.reply(msg)

    elif len(parameters) == required_param_number:
        is_valid_command = False
        if all(param.isdigit() for param in parameters):
            targets_index = [int(param) - 1 for param in parameters]
            id_players = game.get_dead_players() if cmd == "reborn" else game.get_alive_players()
            if all(0 <= i < len(id_players) for i in targets_index):
                is_valid_command = True
                msg = await game.do_player_action(cmd, author.id, *[id_players[i].player_id for i in targets_index])
                await message.reply(msg)

        if not is_valid_command:
            await message.reply(text_template.generate_invalid_command_text(cmd))
    else:
        await message.reply(text_templates.generate_text("not_vote_n_player_text", num=required_param_number))


async def test_player_command(_):
    # TODO:
    pass
