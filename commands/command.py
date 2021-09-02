import discord
import asyncio
from utils import logger
from commands import admin
from config import *



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


async def do_start(game, client, message):
    ''' Start game '''
    game.start()
    await message.channel.send("Game start!")

async def do_stop(game, client, message):
    ''' Stop game '''
    game.stop()
    await message.channel.send("Game stop!")

async def send_text_to_channel(game, text, channel_name):
    ''' Send a message to a channel '''
    guild = game.get_guild()
    channel = discord.utils.get(guild.channels, name=channel_name)
    await channel.send(text)


async def parse_command(game, client, message):
    cmd = message.content.strip().lower().split(' ')[0]
    parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
    # Game commands
    if cmd == '!join':
        await do_join(game, client, message)
    elif cmd == '!leave':
        await do_leave(game, client, message)

    # Admin/Bot commands - User should not directly use these commands
    elif admin.isAdmin(message.author):
        if cmd == '!fstart':
            await do_start(game, client, message)
        elif cmd == '!create_channel': #Test only
            await admin.create_channel(message.author, parameters)
        elif cmd == '!delete_channel': #Test only
            await admin.delete_channel(message.author, parameters)
        elif cmd == '!add': #!add @user1 channel_name
            print(parameters)
            player = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.add_player_to_channel(message.guild, player, channel_name)
        elif cmd == '!remove': #!remove @user1 channel_name
            print(parameters)
            player = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.remove_player_from_channel(message.guild, player, channel_name)


async def test_admin_command(client, guild):
    print("-- Testing admin command --")

    player_id = DISCORD_TESTING_USER1_ID 
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
    await asyncio.sleep(3)
    assert not discord.utils.get(channel.members, name=player.name)

    print("-- End testing admin command --")

async def test_commands(client, guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)
    assert isinstance(client, discord.Client)

    # List all users:
    admin.list_users(guild)

    # Test internal commands
    # TODO:

    # Test admin commands
    await test_admin_command(client, guild)
