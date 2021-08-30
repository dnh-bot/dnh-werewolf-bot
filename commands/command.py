from game import game
from discord.utils import get

async def do_join(client, message):
    ''' Verify author '''
    author = message.author
    game.add_player(author)
    response = "Welcome player {}".format(author)
    # TODO: Reply on GAME_CHANNEL only
    await message.channel.send(response)
    role = get(message.guild.roles, name="Player")
    await message.author.add_roles(role)

async def do_leave(client, message):
    ''' Verify author '''
    author = message.author
    game.remove_player(author)
    response = "Goodbye player {}".format(author)
    await message.channel.send(response)
    role = get(message.guild.roles, name="Player")
    await message.author.remove_roles(role)

async def do_start(client, message):
    ''' Verify author '''
    author = message.author
    game.start()
    await client.reply("Game start")
    
async def do_stop(client, message):
    ''' Verify author '''
    author = message.author
    game.stop()
    await client.reply("Game stop")

async def parse_command(client, message):
    cmd = message.content.strip().lower().split(' ')[0]
    parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
    if cmd == '!join':
        await do_join(client, message)
    elif cmd == '!leave':
        await do_leave(client, message)