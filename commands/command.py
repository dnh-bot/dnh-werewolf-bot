import discord
from utils import logger
from commands import admin
import asyncio


async def do_join(game, client, message):
    ''' Join game '''
    author = message.author
    game.add_player(author)
    response = "Welcome player {}".format(author)
    # TODO: Reply on GAME_CHANNEL only
    await message.channel.send(response)
    role = discord.utils.get(message.guild.roles, name="Player")
    await message.author.add_roles(role)


async def do_leave(game, client, message):
    ''' Leave game '''
    author = message.author
    game.remove_player(author)
    response = "Goodbye player {}".format(author)
    await message.channel.send(response)
    role = discord.utils.get(message.guild.roles, name="Player")
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
    elif cmd == '!add': #!add @user1 channel_name
        if admin.isAdmin(message.author):
            print(parameters)
            player = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.add_player_to_channel(message.guild, player, channel_name)
    elif cmd == '!remove': #!remove @user1 channel_name
        if admin.isAdmin(message.author):
            print(parameters)
            player = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.remove_player_from_channel(message.guild, player, channel_name)


async def test_admin_command(guild, client):
    print("-- Testing admin command --")

    player_id = 640195766186672148 # [𝐒𝖎𝖒𝖕] Sena le Conseiller#0370
    player = guild.get_member(player_id)
    assert isinstance(player, discord.Member)
        
    channel_name = "werewolf"
    channel = discord.utils.get(guild.channels, name=channel_name)
    assert isinstance(channel, discord.TextChannel)

    await admin.add_player_to_channel(guild, player, channel_name)
    await asyncio.sleep(2)
    assert discord.utils.get(channel.members, name=player.name)
    await asyncio.sleep(2)
    await admin.remove_player_from_channel(guild, player, channel_name)
    assert not discord.utils.get(channel.members, name=player.name)

    print("-- End testing admin command --")

async def test_commands(guild, client):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)
    assert isinstance(client, discord.Client)

    # List all users:
    admin.list_users(guild)

    # Test internal commands
    # TODO:

    # Test admin commands
    await test_admin_command(guild, client)
