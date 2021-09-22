from commands import admin, player
import config
from game import text_template

import discord
import asyncio


async def parse_command(client, game, message):
    message_parts = message.content.strip()[len(config.BOT_PREFIX):].split(" ")
    cmd, parameters = message_parts[0], message_parts[1:]
    # Game commands only valid under GAME CATEGORY:
    if admin.is_valid_category(message):
        if cmd == 'join':
            await player.do_join(game, message, force=False)
        elif cmd == 'leave':
            await player.do_leave(game, message, force=False)
        elif cmd == 'start':
            await player.do_start(game, message, force=False)
        elif cmd == 'next':  # Next phase
            await player.do_next(game, message, force=False)
        elif cmd == 'stop':
            await player.do_stop(game, message, force=False)

        elif cmd in ['vote', 'kill', 'guard', 'seer', 'reborn']:
            is_valid_channel = (cmd == 'vote' and message.channel.name == config.GAMEPLAY_CHANNEL) or\
                (cmd == 'kill' and message.channel.name == config.WEREWOLF_CHANNEL) or True
            # TODO: check if cmd guard/seer in the author's personal channel

            if is_valid_channel:
                author = message.author
                is_valid_command = False
                if len(parameters) == 1:
                    if len(message.raw_mentions) == 1:
                        is_valid_command = True
                        msg = await game.do_player_action(cmd, author.id, message.raw_mentions[0])
                        await message.reply(msg)

                    elif parameters[0].isdigit():
                        target_index = int(parameters[0]) - 1
                        alive_players = game.get_alive_players()
                        if 0 <= target_index < len(alive_players):
                            is_valid_command = True
                            target_user = alive_players[target_index]
                            msg = await game.do_player_action(cmd, author.id, target_user.player_id)
                            await message.reply(msg)

                    if not is_valid_command:
                        await message.reply(text_template.generate_invalid_command_text(cmd))

                else:
                    await message.reply(text_template.generate_not_vote_1_player_text())
            else:
                if cmd == 'vote':
                    real_channel = f"#{config.GAMEPLAY_CHANNEL}"
                elif cmd == 'kill':
                    real_channel = f"#{config.WEREWOLF_CHANNEL}"
                else:
                    real_channel = "your personal channel"

                await admin.send_text_to_channel(
                    message.guild, text_template.generate_invalid_channel_text(real_channel), message.channel.name
                )

        elif cmd == 'status':
            await player.do_generate_vote_status_table(message.channel, game.get_vote_status())

        elif cmd == 'timer':
            ''' Usage: 
                `!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
            '''
            if len(parameters) < 3:
                timer_phase = [config.DAYTIME, config.NIGHTTIME, config.ALERT_PERIOD]
                await message.reply(
                    "Use default settings: " +
                    f"dayphase={config.DAYTIME}s, nightphase={config.NIGHTTIME}s, alertperiod={config.ALERT_PERIOD}s"
                )
            else:
                timer_phase = list(map(int, parameters))
                await message.reply(
                    "New settings: " +
                    f"dayphase={timer_phase[0]}s, nightphase={timer_phase[1]}s, alertperiod={timer_phase[2]}s"
                )
            game.set_timer_phase(timer_phase)

        elif cmd == 'timerstart':
            game.timer_stopped = False
            await message.reply(text_template.generate_timer_start_text())
        elif cmd == 'timerstop':
            game.timer_stopped = True
            await message.reply(text_template.generate_timer_stop_text())


    # Admin/Bot commands - User should not directly use these commands
    if admin.is_admin(message.author):
        if cmd == 'fcreate_channel':  # Test only
            await admin.create_channel(message.guild, client.user, parameters[0])
        elif cmd == 'fdelete_channel':  # Test only
            await admin.delete_channel(message.guild, client.user, parameters[0])
        elif cmd == 'fcreate':  # Create game channels
            if len(message.mentions) == 1:
                user = message.mentions[0]
                if user.id == client.user.id:
                    await admin.create_category(message.guild, client.user, config.GAME_CATEGORY)
                    await admin.create_channel(message.guild, client.user, config.LOBBY_CHANNEL, is_public=True)
                    await admin.create_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL, is_public=False)
            else:
                await message.reply("Missing @bot_name")
        elif cmd == "fdelete":  # Delete all channels and category under config.GAME_CATEGORY
            if len(message.mentions) == 1:
                user = message.mentions[0]
                try:
                    if user.id == client.user.id:
                        await admin.delete_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL)
                        await admin.delete_channel(message.guild, client.user, config.WEREWOLF_CHANNEL)
                        await admin.delete_channel(message.guild, client.user, config.CEMETERY_CHANNEL)
                        await admin.delete_all_personal_channel(message.guild)
                        await admin.delete_channel(message.guild, client.user, config.LOBBY_CHANNEL)
                        await admin.delete_category(message.guild, client.user)
                except Exception as e:
                    print(e)
            else:
                await message.reply("Missing @bot_name")
        elif cmd == 'fadd':  # !add @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters[1]
            await admin.add_user_to_channel(message.guild, user, channel_name, is_read=True, is_send=True)
        elif cmd == 'fremove':  # !remove @user1 channel_name
            print(parameters)
            user = message.mentions[0]
            channel_name = parameters[1]
            await admin.remove_user_from_channel(message.guild, user, channel_name)
        elif cmd == 'fend':
            await game.stop()
        elif admin.is_valid_category(message):
            if cmd == "fjoin":
                await admin.create_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL, is_public=False)
                await player.do_join(game, message, force=True)
            elif cmd == "fleave":
                await player.do_leave(game, message, force=True)
            elif cmd == "fstart":
                await player.do_start(game, message, force=True)
            elif cmd == 'fnext':  # Next phase
                await player.do_next(game, message, force=True)
            elif cmd == 'fstop':
                await player.do_stop(game, message, force=True)
            elif cmd == "fclean":  # Delete all private channels under config.GAME_CATEGORY
                try:
                    await admin.delete_channel(message.guild, client.user, config.GAMEPLAY_CHANNEL)
                    await admin.delete_channel(message.guild, client.user, config.WEREWOLF_CHANNEL)
                    await admin.delete_channel(message.guild, client.user, config.CEMETERY_CHANNEL)
                    await admin.delete_all_personal_channel(message.guild)
                except Exception as e:
                    print(e)
            elif cmd == "fdebug":
                # print(asyncio.all_tasks())
                exec(" ".join(parameters))
        else:
            await message.reply(f"{message.author} used invalid Admin command.")


async def test_commands(guild):
    print("Testing admin command")
    assert isinstance(guild, discord.Guild)

    # List all users:
    admin.list_users(guild)

    # Test player commands
    await player.test_player_command(guild)

    # Test admin commands
    await admin.test_admin_command(guild)
