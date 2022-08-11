"""
This provides APIs for Player role
"""
import time
import math
import discord
import config
from commands import admin
from game import text_template


def check_vote_valid(num_votes, num_players, task_name):
    if task_name == "start" and num_players < 4:
        return False, f"At least 4 players to {task_name} game."

    if num_votes / num_players <= config.VOTE_RATE:
        return False, f"(vote rate {num_votes}/{num_players}). Need at least {math.floor(num_players * config.VOTE_RATE) + 1} votes"
    else:
        return True, f"Enough votes to proceed `{task_name}`"  # Should never see it :D


async def do_join(game, message, force=False):
    """Join game"""
    if not game.is_started():
        if force:
            if not message.mentions:
                await message.reply(text_template.generate_invalid_command_text("fjoin"))
            else:
                for user in message.mentions:
                    joined_players = await game.add_player(user.id, user.name)
                    if joined_players > 0:
                        await message.channel.send(text_template.generate_join_text(user.display_name, joined_players))
                    else:
                        await message.channel.send(text_template.generate_already_in_game_text())
        else:
            joined_players = await game.add_player(message.author.id, f"{message.author.name}-{message.author.discriminator}")
            if joined_players > 0:
                await message.channel.send(text_template.generate_join_text(message.author.display_name, joined_players))
            else:
                await message.channel.send(text_template.generate_already_in_game_text())
    else:
        await message.reply(text_template.generate_game_already_started_text())


async def do_leave(game, message, force=False):
    """Leave game"""
    if not game.is_started():
        if force:
            if not message.mentions:
                await message.reply(text_template.generate_invalid_command_text("fleave"))
            else:
                for user in message.mentions:
                    joined_players = await game.remove_player(user.id)
                    if joined_players >= 0:
                        await message.channel.send(text_template.generate_leave_text(user.display_name, joined_players))
                    else:
                        await message.channel.send(text_template.generate_not_in_game_text())
        else:
            joined_players = await game.remove_player(message.author.id)
            if joined_players >= 0:
                await message.channel.send(text_template.generate_leave_text(message.author.display_name, joined_players))
            else:
                await message.channel.send(text_template.generate_not_in_game_text())
    else:
        await message.reply(text_template.generate_game_already_started_text())


async def do_watch(game, message):
    """Watch game"""
    watched_players = await game.add_watcher(message.author.id)
    if watched_players > 0:
        await message.channel.send(text_template.generate_watch_text(message.author.display_name, watched_players))
    elif watched_players == -1:
        await message.channel.send(text_template.generate_already_watched_game_text())
    elif watched_players == -2:
        await message.channel.send(text_template.generate_already_in_game_text() + " Bạn không thể ấn theo dõi nữa :v")


async def do_unwatch(game, message):
    """Unwatch game"""
    watched_players = await game.remove_watcher(message.author.id)
    if watched_players >= 0:
        await message.channel.send(text_template.generate_unwatch_text(message.author.display_name, watched_players))
    elif watched_players == -1:
        await message.channel.send(text_template.generate_not_watched_game_text())
    elif watched_players == -2:
        await message.channel.send(text_template.generate_already_in_game_text() + " Bạn không được bỏ theo dõi đâu :v")


# Require at least 2 players to start the game
async def do_start(game, message, force=False):
    """Start game"""
    if not game.is_started():
        if force:
            await game.start()
            await message.channel.send(text_template.generate_game_started_text())
        else:
            if message.author.id not in game.players:
                await message.reply(text_template.generate_not_in_game_text())
            else:
                game.vote_start.add(message.author.id)
                valid, text = check_vote_valid(len(game.vote_start), len(game.players), "start")
                if valid:
                    await game.start()
                    await message.channel.send(text_template.generate_game_started_text())
                else:
                    await message.reply(text_template.generate_vote_for_game_text("start", message.author.display_name, text))
    else:
        await message.reply(text_template.generate_game_already_started_text())


async def do_next(game, message, force=False):
    """Next phase"""
    if game.is_started():
        if force:
            await game.next_phase_cmd()
        else:
            if time.time() - game.get_last_nextcmd_time() > config.NEXT_CMD_DELAY:
                # User needs to wait for next phase
                if message.author.id not in game.players:
                    await message.reply(text_template.generate_not_in_game_text())
                else:
                    game.vote_next.add(message.author.id)
                    valid, text = check_vote_valid(len(game.vote_next), len(game.get_alive_players()), "next")
                    if valid:
                        await game.next_phase_cmd()
                    else:
                        await message.reply(text_template.generate_vote_for_game_text("next", message.author.display_name, text))
            else:
                await message.reply(text_template.generate_too_quick(time.time(), game.get_last_nextcmd_time()))
    else:
        await message.reply(text_template.generate_game_not_started_text())


# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stopgame` to end the game
async def do_stop(game, message, force=False):
    """Stop game"""
    if game.is_started():
        if force:
            await message.channel.send(text_template.generate_game_stop_text())
            await game.stop()
        else:
            if message.author.id not in game.players:
                await message.reply(text_template.generate_not_in_game_text())
            else:
                game.vote_stop.add(message.author.id)
                valid, text = check_vote_valid(len(game.vote_stop), 1 if game.is_ended() else 2, "stop")
                if valid:
                    await message.reply(text_template.generate_game_stop_text())
                    await game.stop()
                else:
                    await message.reply(text_template.generate_vote_for_game_text("stop", message.author.display_name, text))
    else:
        await message.reply(text_template.generate_game_not_started_text())


async def do_generate_vote_status_table(channel, table, table_description=""):
    # Table format: {"u2": {"u1"}, "u1": {"u3", "u2"}}
    # @user1:
    # | Votes: 2
    # | Voters: @user2, @user3
    #
    # @user2:
    # | Votes: 1
    # | Voters: @user1

    if not table:
        if table is None and table_description:
            await channel.send(table_description)
        else:
            await channel.send(text_template.generate_nobody_voted_text())
        return

    vote_table = {}
    for k, v in table.items():
        member_k = channel.guild.get_member(k)
        if member_k is not None:
            name_field = member_k.display_name
        else:
            name_field = str(k)

        vote_table[name_field] = v

    await admin.send_embed_to_channel(
        channel.guild, text_template.generate_vote_table_embed(vote_table, table_description), channel.name
    )


async def do_generate_status_table(channel, game_status, remaining_time, table, table_description=""):
    # Table format: {"u2": {"u1"}, "u1": {"u3", "u2"}}
    # ->
    # table_description
    # - @user1: 2 phiếu (@user2, @user3)
    # - @user2: 1 phiếu (@user1)

    if not table:
        if table is None and table_description:
            vote_table = None
        else:
            vote_table = {}
    else:
        vote_table = {}
        for k, v in table.items():
            member_k = channel.guild.get_member(k)
            if member_k is not None:
                name_field = f'<@!{k}>'
            else:
                name_field = str(k)

            vote_table[name_field] = sorted(v)

    await admin.send_embed_to_channel(
        channel.guild, text_template.generate_status_embed(
            game_status, remaining_time, vote_table, table_description), channel.name
    )


async def test_player_command(guild):
    # TODO:
    pass
