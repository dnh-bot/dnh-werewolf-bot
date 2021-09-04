'''
This provides APIs for Player role
'''

import discord
import config
from game import text_template as tt

async def do_join(guild, channel, user):
    ''' Join game '''
    # response = "Welcome player {}".format(author)
    response = tt.generate_join_text(user.name)
    # TODO: Reply on GAME_CHANNEL only
    await channel.send(response)
    role = discord.utils.get(guild.roles, name="Player")
    await user.add_roles(role)


async def do_leave(guild, channel, user):
    ''' Leave game '''
    response = "Goodbye player {}".format(user)
    await channel.send(response)
    role = discord.utils.get(guild.roles, name="Player")
    await user.remove_roles(role)

# Require at least 2 players to start the game
async def do_start(message):
    ''' Start game '''
    await message.channel.send(f"Game started in #{config.GAMEPLAY_CHANNEL} ! (Only Player can view)")

# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stop` to end the game
async def do_stop(message):
    ''' Stop game '''
    await message.channel.send("Game stop!")



async def test_player_command(guild):
    # TODO: 
    pass
