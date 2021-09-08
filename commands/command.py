import discord
import asyncio
from commands import admin, player
import config


async def parse_command(game, message):
    message_parts = message.content.strip().lower()[len(config.BOT_PREFIX):].split(" ")
    cmd, parameters = message_parts[0], message_parts[1:]
    # Game commands
    if cmd == 'join':
        if game.is_started():
            text = "Game started. Please wait until next game!"
            await admin.send_text_to_channel(message.guild, text, message.channel.name)
        elif game.add_player(message.author.id, message.author.name):
            # await admin.create_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_public=False)
            await player.do_join(message.guild, message.channel, message.author)
            await admin.add_user_to_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True)
        else:
            await message.reply("You have already joined.")
    elif cmd == 'leave':
        if game.is_started():
            await admin.send_text_to_channel(message.guild, "Game started. Please wait until next game!", message.channel.name)
        elif game.remove_player(message.author.id):
            await player.do_leave(message.guild, message.channel, message.author)
            await admin.remove_user_from_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL)
        else:
            await message.reply("You are not in the game.")
    elif cmd == 'start':
        await player.do_start(game, message, force=False)
    elif cmd == 'next':  # Next phase
        await player.do_next(game, message, force=False)
    elif cmd == 'stop':
        await player.do_stop(game, message, force=False)
    elif cmd == 'vote':  # author: `!vote @target_user`
        if message.channel.name != config.GAMEPLAY_CHANNEL:
            await admin.send_text_to_channel(message.guild, f"Command in invalid channel. Please use in #{config.GAMEPLAY_CHANNEL}", message.channel.name)
        elif len(message.mentions) == 1:
            author = message.author
            msg = await game.vote(author.id, message.mentions[0].id)
            await message.reply(msg)
        else:
            await admin.send_text_to_channel(message.guild, "Invalid command", message.channel.name)

    elif cmd == 'kill':  # author: `!kill @target_user`
        if message.channel.name != config.WEREWOLF_CHANNEL:
            await admin.send_text_to_channel(message.guild, f"Command {config.BOT_PREFIX}kill only available in #{config.WEREWOLF_CHANNEL}", message.channel.name)
        elif len(message.mentions) == 1:
            author = message.author
            msg = await game.kill(author.id, message.mentions[0].id)
            await message.reply(msg)
        else:
            await message.reply(f"Invalid command. Use: `{config.BOT_PREFIX}kill @target_user`")

    elif cmd == 'status':
        await player.do_generate_vote_status_table(message.channel, game.get_vote_status())

    elif cmd == 'timer':
        ''' Usage: 
            `!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
        '''
        if len(parameters) < 3:
            timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
            await message.reply(f"Use default setting: dayphase=60s, nightphase=30s, alertperiod=20s")
        else:
            timer_phase = list(map(int, parameters))
        game.set_timer_phase(timer_phase)

    elif cmd == 'timerstart':
        game.timer_stopped = False
        await message.reply("Timer start!")
    elif cmd == 'timerstop':
        game.timer_stopped = True
        await message.reply("Timer stopped!")

    # Admin/Bot commands - User should not directly use these commands
    elif admin.isAdmin(message.author):
        if cmd == 'fcreate_channel':  # Test only
            await admin.create_channel(message.guild, message.author, parameters)
        elif cmd == 'fdelete_channel':  # Test only
            await admin.delete_channel(message.guild, message.author, parameters)
        elif cmd == 'fcreate':  # Create game channels
            await admin.create_category(message.guild, message.author, config.GAME_CATEGORY)
            await admin.create_channel(message.guild, message.author, config.LOBBY_CHANNEL, is_public=True)
            await admin.create_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_public=False)
        elif cmd == 'fadd':  # !add @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.add_user_to_channel(message.guild, user, channel_name, is_read=True, is_send=True)
        elif cmd == 'fremove':  # !remove @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters.split(' ')[1]
            await admin.remove_user_from_channel(message.guild, user, channel_name)
        elif cmd == 'fend':
            await game.stop()
        elif cmd == "fjoin":
            if game.is_started():
                text = "Game started. Please wait until next game!"
                await admin.send_text_to_channel(message.guild, text, message.channel.name)
            else:
                if not message.mentions:
                    await admin.send_text_to_channel(message.guild, f"Invalid Command.\nUsage: {config.BOT_PREFIX}fjoin @user1 @user2 ...", message.channel.name)
                else:
                    await admin.create_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL, is_public=False)
                    for user in message.mentions:
                        await player.do_join(message.guild, message.channel, user)
                        game.add_player(user.id, user.name)
                        await admin.add_user_to_channel(message.guild, user, config.GAMEPLAY_CHANNEL, is_read=True, is_send=True)

        elif cmd == "fleave":
            if game.is_started():
                await admin.send_text_to_channel(message.guild, "Game started. Please wait until next game!", message.channel.name)
            else:
                if not message.mentions:
                    await admin.send_text_to_channel(message.guild, f"Invalid Command\nUsage: {config.BOT_PREFIX}fleave @user1 @user2 ...", message.channel.name)
                for user in message.mentions:
                    await player.do_leave(message.guild, message.channel, user)
                    game.remove_player(user.id)
                    await admin.remove_user_from_channel(message.guild, user, config.GAMEPLAY_CHANNEL)

        elif cmd == "fstart":
            await player.do_start(game, message, force=True)
        elif cmd == 'fnext':  # Next phase
            await player.do_next(game, message, force=True)
        elif cmd == 'fstop':
            await player.do_stop(game, message, force=True)
        elif cmd == "fclean":
            try:
                await admin.delete_channel(message.guild, message.author, config.GAMEPLAY_CHANNEL)
                await admin.delete_channel(message.guild, message.author, config.WEREWOLF_CHANNEL)
                await admin.delete_all_personal_channel(message.guild)
            except Exception as e:
                print(e)
        elif cmd == "fdebug":
            # print(asyncio.all_tasks())
            exec(" ".join(parameters))
    else:
        await message.reply(f"{message.author} is not Admin role")


async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
