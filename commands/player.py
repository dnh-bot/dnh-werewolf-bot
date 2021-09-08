'''
This provides APIs for Player role
'''
import time
import math
import discord
import config
from game import text_template as tt

last_next = time.time()

def check_vote_valid(num_votes, num_players, task_name):
    if num_players < 4:
        return False, f"At least 4 players to {task_name} game."

    if num_votes / num_players <= config.VOTE_RATE:
        return False, f"(vote rate {num_votes}/{num_players}). Need at least {math.floor(num_players * config.VOTE_RATE) + 1} votes"
    else:
        return True, f"Enough votes to proceed `{task_name}`"  # Should never see it :D


async def do_join(guild, channel, user):
    ''' Join game '''
    response = tt.generate_join_text(user.display_name)
    await channel.send(response)


async def do_leave(guild, channel, user):
    ''' Leave game '''
    response = "Goodbye player {}".format(user.display_name)
    await channel.send(response)


# Require at least 2 players to start the game
async def do_start(game, message, force=False):
    ''' Start game '''
    if not game.is_started():
        if force:
            await game.start()
            await message.channel.send(f"Game started in #{config.GAMEPLAY_CHANNEL} ! (Only Player can view)")
        else:
            if message.author.id not in game.players:
                await message.reply("You are not in the game.")
            else:
                game.vote_start.add(message.author.id)
                valid, text = check_vote_valid(len(game.vote_start), len(game.players),  "start")
                if valid:
                    await game.start()
                    await message.channel.send(f"Game started in #{config.GAMEPLAY_CHANNEL} ! (Only Player can view)")
                else:
                    await message.reply(f"Player {message.author.display_name} votes for start game. {text}")
    else:
        await message.reply("Game already started")


async def do_next(game, message, force=False):
    ''' Next phase '''
    if game.is_started():
        global last_next
        if force:
            last_next = time.time()
            await game.next_phase()
        else:
            if time.time() - last_next > config.NEXT_CMD_DELAY:  # User needs to wait at least 60s for next phase
                if message.author.id not in game.players:
                    await message.reply("You are not in the game.")
                else:
                    game.vote_next.add(message.author.id)
                    valid, text = check_vote_valid(len(game.vote_next), len(game.players), "next")
                    if valid:
                        last_next = time.time()
                        await game.next_phase()
                    else:
                        await message.reply(f"Player {message.author.display_name} votes for next phase. {text}")
            else:
                await message.reply(f"Run `!next` command too quick, please wait for {config.NEXT_CMD_DELAY - time.time() + last_next:.1f} seconds")
    else:
        await message.reply("Game has not started yet!")


# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stop` to end the game
async def do_stop(game, message, force=False):
    ''' Stop game '''
    if game.is_started():
        if force:
            await message.channel.send("Game stops!")
            await game.stop()
        else:
            if message.author.id not in game.players:
                await message.reply("You are not in the game.")
            else:
                game.vote_stop.add(message.author.id)
                valid, text = check_vote_valid(len(game.vote_stop), len(game.players),  "stop")
                if valid:
                    await message.reply("Game stops!")
                    await game.stop()
                else:
                    await message.reply(f"Player {message.author.display_name} votes for stop game. {text}")
    else:
        await message.reply("Game has not started yet!")


async def do_generate_vote_status_table(channel, table):
    # Table format: {'u2': {'u1'}, 'u1': {'u3', 'u2'}}
    # Player | Number of votes | Voters
    #  u1             2           u2, u3
    #  u2             1           u1
    if not table:
        await channel.send("Nobody has voted yet")
        return
    victim_list = []
    voter_count = []
    voter_list = []
    for k, v in table.items():
        victim_list.append(f"<@{k}>")
        voter_count.append(f"   {len(v)}")
        voter_list.append(",".join([f"<@{i}>" for i in v]))
    # print("\n".join(victim_list))
    # print("\n".join(voter_count))
    # print("\n".join(voter_list))
    embed = discord.Embed(title='Vote Results', description=None)
    embed.add_field(name="Player",          value="\n".join(victim_list), inline=True)
    embed.add_field(name="Votes",           value="\n".join(voter_count), inline=True)
    embed.add_field(name="Voters",          value="\n".join(voter_list), inline=True)
    await channel.send(embed=embed)


async def test_player_command(guild):
    # TODO: 
    pass
