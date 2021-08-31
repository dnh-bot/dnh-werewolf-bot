from utils import logger
from game import game
from discord.utils import get
from commands import admin


async def do_join(game, client, message):
    ''' Join game '''
    author = message.author
    game.add_player(author)
    response = "Welcome player {}".format(author)
    # TODO: Reply on GAME_CHANNEL only
    await message.channel.send(response)
    role = get(message.guild.roles, name="Player")
    await message.author.add_roles(role)


async def do_leave(game, client, message):
    ''' Leave game '''
    author = message.author
    game.remove_player(author)
    response = "Goodbye player {}".format(author)
    await message.channel.send(response)
    role = get(message.guild.roles, name="Player")
    await message.author.remove_roles(role)


async def do_start(client, message):
    ''' Start game '''
    author = message.author
    game.start()
    await client.reply("Game start")
    

async def do_stop(client, message):
    ''' Stop game '''
    author = message.author
    game.stop()
    await client.reply("Game stop")


async def parse_command(game, client, message):
    cmd = message.content.strip().lower().split(' ')[0]
    parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
    if cmd == '!join':
        await do_join(game, client, message)
    elif cmd == '!leave':
        await do_leave(game, client, message)
    elif cmd == '!fstart':
        if admin.isAdmin(message.author):
            do_start(client, message)
    elif cmd == '!create_channel': #Test only
        if admin.isAdmin(message.author):
            await admin.create_channel(message.author, parameters)
    elif cmd == '!delete_channel': #Test only
        if admin.isAdmin(message.author):
            await admin.delete_channel(message.author, parameters)



