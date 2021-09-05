import discord
import asyncio
from commands import admin, player
import config
import time

last_next = time.time()


async def parse_command(game, message):
    cmd = message.content.strip().lower().split(' ')[0]
    parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
    # Game commands
    if cmd == '!join':
        if game.is_started():
            text = "Game started. Please wait until next game!"
            await admin.send_text_to_channel(message.guild, text, message.channel.name)
        elif game.add_player(message.author.id):
            await admin.create_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_public=False)
            await player.do_join(message.guild, message.channel, message.author)
            await admin.add_user_to_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL)
        else:
            await message.reply("You have already joined.")
    elif cmd == '!leave':
        if game.is_started():
            await admin.send_text_to_channel(message.guild, "Game started. Please wait until next game!", message.channel.name)
        elif game.remove_player(message.author.id):
            await player.do_leave(message.guild, message.channel, message.author)
            await admin.remove_user_from_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL)
        else:
            await message.reply("You are not in the game.")
    elif cmd == '!start':
        await player.do_start(game, message)
    elif cmd == '!stop':
        await player.do_stop(game, message)
    elif cmd == '!vote': # author: `!vote @target_user`
        author = message.author
        if len(message.mentions)<1:
            await admin.send_text_to_channel(message.guild, "Invalid command", message.channel.name)
        elif message.channel.name != config.GAMEPLAY_CHANNEL:
            await admin.send_text_to_channel(message.guild, f"Command in invalid channel. Please use in #{config.GAMEPLAY_CHANNEL}", message.channel.name)
        else:
            msg = await game.vote(author.id, message.mentions[0].id)
            await admin.send_text_to_channel(message.guild, msg, message.channel.name)
    elif cmd == '!kill': # author: `!kill @target_user`
        if message.channel.name != config.WEREWOLF_CHANNEL:
            await admin.send_text_to_channel(message.guild, f"Command {config.BOT_PREFIX}kill only available in #{config.WEREWOLF_CHANNEL}", message.channel.name)
        author = message.author
        target_user = message.mentions[0]
        msg = await game.kill(author.id, target_user.id)
        await admin.send_text_to_channel(message.guild, msg, message.channel.name)
    elif cmd == '!status':
        await player.do_generate_vote_status_table(message.channel, game.get_vote_status())


    # Admin/Bot commands - User should not directly use these commands
    elif admin.isAdmin(message.author):
        if cmd == '!create_channel':  # Test only
            await admin.create_channel(message.guild, message.author, parameters)
        elif cmd == '!delete_channel':  # Test only
            await admin.delete_channel(message.guild, message.author, parameters)
        elif cmd == '!create':  # Create game channels
            await admin.create_category(message.guild, message.author, config.GAME_CATEGORY)
            await admin.create_channel(message.guild, message.author, config.LOBBY_CHANNEL, is_public=True)
            await admin.create_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_public=False)
        elif cmd == '!add':  # !add @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.add_user_to_channel(message.guild, user, channel_name)
        elif cmd == '!remove':  # !remove @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.remove_user_from_channel(message.guild, user, channel_name)
        elif cmd == '!next':  # Next phase
            global last_next
            if time.time() - last_next > config.NEXT_CMD_DELAY:
                last_next = time.time()
                await game.next_phase()
            else:
                await admin.send_text_to_channel(message.guild, f"Run !next command too quick, please wait for {config.NEXT_CMD_DELAY - time.time() + last_next:.1f} seconds", message.channel.name)
        elif cmd == '!end':
            await game.stop()
        elif cmd == "!fjoin":
            if game.is_started():
                text = "Game started. Please wait until next game!"
                await admin.send_text_to_channel(message.guild, text, message.channel.name)
            else:
                if not message.mentions:
                    await admin.send_text_to_channel(message.guid, "Invalid Command.\nUsage: !fjoin @user1 @user2 ...", message.channel.name)
                else:
                    await admin.create_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_public=False)
                    for user in message.mentions:
                        await player.do_join(message.guild, message.channel, user)
                        game.add_player(user.id)
                        await admin.add_user_to_channel(message.guild, user, config.GAMEPLAY_CHANNEL)
        elif cmd == "!fleave":
            if game.is_started():
                await admin.send_text_to_channel(message.guild, "Game started. Please wait until next game!", message.channel.name)
            else:
                if not message.mentions:
                    await admin.send_text_to_channel(message.guid, "Invalid Command\nUsage: !fleave @user1 @user2 ...", message.channel.name)
                for user in message.mentions:
                    await player.do_leave(message.guild, message.channel, user)
                    game.remove_player(user.id)
                    await admin.remove_user_from_channel(message.guild, user, config.GAMEPLAY_CHANNEL)


async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
