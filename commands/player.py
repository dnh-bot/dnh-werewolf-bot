'''
This provides APIs for Player role
'''

import discord
import config
from game import text_template as tt

async def do_join(message):
    ''' Join game '''
    author = message.author
    # response = "Welcome player {}".format(author)
    response = tt.generate_join_text(author.name)
    # TODO: Reply on GAME_CHANNEL only
    await message.channel.send(response)
    role = discord.utils.get(message.guild.roles, name="Player")
    await message.author.add_roles(role)


async def do_leave(message):
    ''' Leave game '''
    author = message.author
    response = "Goodbye player {}".format(author)
    await message.channel.send(response)
    role = discord.utils.get(message.guild.roles, name="Player")
    await message.author.remove_roles(role)

# Require at least 2 players to start the game
async def do_start(message):
    ''' Start game '''
    await message.channel.send("Game start!")

# Player can call stop game when they want to finish game regardless current game state
# Need 2/3 players type: `!stop` to end the game
async def do_stop(message):
    ''' Stop game '''
    await message.channel.send("Game stop!")



async def test_player_command(guild):
    # TODO: 
    pass