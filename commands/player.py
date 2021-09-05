'''
This provides APIs for Player role
'''

import discord
import config
from game import text_template as tt

async def do_join(guild, channel, user):
    ''' Join game '''
    response = tt.generate_join_text(user.display_name)
    await channel.send(response)


async def do_leave(guild, channel, user):
    ''' Leave game '''
    response = "Goodbye player {}".format(user.display_name)
    await channel.send(response)

# Require at least 2 players to start the game
async def do_start(game, message):
    ''' Start game '''
    if message.author.id not in game.player_id:
        return await message.reply("You are not in the game.")

    game.vote_start.add(message.author.id)

    num_players = len(game.player_id)
    num_vote = len(game.vote_start)

    if num_players < 4:
        return await message.reply("At least 4 players to start game.")

    text = f"Player {message.author.display_name} votes for start the game. (vote rate {num_vote}/{num_players})"
    print(text)
    await message.channel.send(text)

    if num_vote / num_players < 2/3: return

    await game.start()
    await message.channel.send(f"Game started in #{config.GAMEPLAY_CHANNEL} ! (Only Player can view)")

# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stop` to end the game
async def do_stop(game, message):
    ''' Stop game '''
    if message.author.id not in game.player_id:
        return await message.reply("You are not in the game.")

    game.vote_stop.add(message.author.id)

    num_players = len(game.player_id)
    num_vote = len(game.vote_stop)

    text = f"Player {message.author.display_name} votes for stop the game. (vote rate {num_vote}/{num_players})"
    print(text)
    await message.channel.send(text)

    if num_vote / num_players < 2/3: return

    await message.channel.send("Game stop!")
    await game.stop()



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
        voter_count.append(f"   {str(len(v))}")
        voter_list.append(",".join([f"<@{i}>" for i in v]))
    # print("\n".join(victim_list))
    # print("\n".join(voter_count))
    # print("\n".join(voter_list))
    embed = discord.Embed(title = 'Vote Results', description = None)
    embed.add_field(name="Player",          value="\n".join(victim_list), inline=True)
    embed.add_field(name="Votes",           value="\n".join(voter_count), inline=True)
    embed.add_field(name="Voters",          value="\n".join(voter_list), inline=True)
    await channel.send(embed=embed)

async def test_player_command(guild):
    # TODO: 
    pass
