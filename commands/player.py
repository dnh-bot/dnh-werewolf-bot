"""
This provides APIs for Player role
"""
import time
import math
import discord
import config
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
            joined_players = await game.add_player(message.author.id, message.author.name)
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
            await game.next_phase()
        else:
            if time.time() - game.get_last_nextcmd_time() > config.NEXT_CMD_DELAY:
                # User needs to wait for next phase
                if message.author.id not in game.players:
                    await message.reply(text_template.generate_not_in_game_text())
                else:
                    game.vote_next.add(message.author.id)
                    valid, text = check_vote_valid(len(game.vote_next), len(game.get_alive_players()), "next")
                    if valid:
                        await game.next_phase()
                    else:
                        await message.reply(text_template.generate_vote_for_game_text("next", message.author.display_name, text))
            else:
                await message.reply(text_template.generate_too_quick(time.time(), game.get_last_nextcmd_time()))
    else:
        await message.reply(text_template.generate_game_not_started_text())


# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stop` to end the game
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
                valid, text = check_vote_valid(len(game.vote_stop), 1, "stop")
                if valid:
                    await message.reply(text_template.generate_game_stop_text())
                    await game.stop()
                else:
                    await message.reply(text_template.generate_vote_for_game_text("stop", message.author.display_name, text))
    else:
        await message.reply(text_template.generate_game_not_started_text())


async def do_generate_vote_status_table(channel, table):
    # Table format: {"u2": {"u1"}, "u1": {"u3", "u2"}}
    # @user1:
    # | Votes: 2
    # | Voters: @user2, @user3
    #
    # @user2:
    # | Votes: 1
    # | Voters: @user1

    if not table:
        await channel.send(text_template.generate_nobody_voted_text())
        return
    embed = discord.Embed(title="Vote Results", description="Danh sách những kẻ có khả năng bị hành hình")
    for k, v in table.items():
        player = channel.guild.get_member(k).display_name
        votes = len(v)
        voters = ",".join([f"<@!{i}>" for i in v])
        embed.add_field(name=f"{player}", value="\n".join((f"Votes: {votes}", f"Voters: {voters}")), inline=False)
    # embed_data = zip(victim_list, tuple(zip(voter_count, voter_list)))
    # print("\n".join(victim_list))
    # print("\n".join(voter_count))
    # print("\n".join(voter_list))
    
    # for victim, field_value in embed_data:
    #     embed.add_field(name=victim, value="\n".join(field_value), inline=False)
    await channel.send(embed=embed)


async def test_player_command(guild):
    # TODO: 
    pass
