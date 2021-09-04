import discord
import asyncio
from commands import admin, player


async def parse_command(game, message):
    cmd = message.content.strip().lower().split(' ')[0]
    parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
    # Game commands
    if cmd == '!join':
        await player.do_join(message)
        game.add_player(message.author.id)
    elif cmd == '!leave':
        await player.do_leave(message)
        game.remove_player(message.author.id)
    elif cmd == '!start':
        await player.do_start(message)
        await game.start()
    elif cmd == '!stop':
        await player.do_stop(message)
        await game.stop()
    elif cmd == '!vote': # author: `!vote @target_user`
        author = message.author
        target_user = message.mentions[0]
        await game.vote(author.id, target_user.id)
    elif cmd == '!kill': # author: `!kill @target_user`
        author = message.author
        target_user = message.mentions[0]
        await game.kill(author.id, target_user.id)

    # Admin/Bot commands - User should not directly use these commands
    elif admin.isAdmin(message.author):
        if cmd == '!create_channel': #Test only
            await admin.create_channel(message.guild, message.author, parameters)
        elif cmd == '!delete_channel': #Test only
            await admin.delete_channel(message.guild, message.author, parameters)
        elif cmd == '!add': #!add @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.add_player_to_channel(message.guild, user, channel_name)
        elif cmd == '!remove': #!remove @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.remove_player_from_channel(message.guild, user, channel_name)



async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
