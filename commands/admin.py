
'''
This provides APIs for Admin role and bot role
'''

import discord
import asyncio
from utils import logger
import config


def isAdmin(author):
    # Check if this user has 'Admin' right
    admin_role = discord.utils.get(author.roles, name="Admin")
    if admin_role in author.guild.roles:
        return True
    else:
        print(f"{author.display_name} is not Admin Role")
        return False

def list_users(guild):
    print("Server member: ")
    for user in guild.members:
        print("- ", user.display_name, user.id)
    print("-------------")

async def create_category(guild, author, category_name):
    # Create a category with limited permissions
    # Only the author and Admin roles can view this category
    print("Try creating category_name=", category_name)
    existing_category = discord.utils.get(guild.categories, name=category_name)
    if not existing_category:
        try:
            admin_role = discord.utils.get(guild.roles, name="Admin")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            response = "{} created category {}".format(author.name, category_name)
            print(response)
            category = await guild.create_category(category_name, overwrites=overwrites)
            return category
        except Exception as e:
            print(e)
    return existing_category

async def create_channel(guild, author, channel_name, category_name=config.GAME_CATEGORY, is_public=False):
    # Create text channel with limited permissions
    # Only the author and Admin roles can view this channel
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        try:
            admin_role = discord.utils.get(guild.roles, name="Admin")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=is_public),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            response = "{} created channel {}".format(author.name, channel_name)
            print(response)
            category = discord.utils.get(guild.categories, name=category_name)
            logger.logger_debug(category)
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
            await asyncio.sleep(1)
            await channel.send(response)
            return channel
        except Exception as e:
            print(e)
    return existing_channel

async def delete_channel(guild, author, channel_name):
    # Delete text channel. Any Admin can delete it
    try:
        channel = discord.utils.get(guild.channels, name=channel_name)
        response = "{} deleted channel {}".format(author.display_name, channel_name)
        assert isinstance(channel, discord.TextChannel)
        print(response)
        # await channel.send(response)
        await channel.delete()
    except Exception as e:
        print(e)
        print(channel_name, author)

async def add_user_to_channel(guild, user, channel_name):
    # Add a user to specific channel
    print("===", user, channel_name)
    # logger.logger_debug(guild.channels)
    channel = discord.utils.get(guild.channels, name=channel_name)
    try:
        await channel.set_permissions(user, read_messages=True, send_messages=True)
        print("Successfully added ", user, " to ", channel_name)
    except Exception as e:
        print(e)
        print(channel_name, user)

async def remove_user_from_channel(guild, user, channel_name):
    # Add a user to specific channel
    print("===", user, channel_name)
    channel = discord.utils.get(guild.channels, name=channel_name)
    try:
        await channel.set_permissions(user, read_messages=False, send_messages=False)
        print("Successfully removed ", user, " from ", channel_name)
    except Exception as e:
        print(e)
        print(channel_name, user)


async def send_text_to_channel(guild, text, channel_name):
    ''' Send a message to a channel '''
    channel = discord.utils.get(guild.channels, name=channel_name)
    try:
        await channel.send(text)
    except Exception as e:
        print(e)
        print(channel_name)


async def test_admin_command(guild):
    print("-- Testing admin command --")
    user_id = config.DISCORD_TESTING_USER1_ID 
    public_user = guild.get_member(user_id)
    assert isinstance(public_user, discord.Member)

    admin_id = config.DISCORD_TESTING_ADMIN1_ID
    admin_user = guild.get_member(admin_id)
    assert isinstance(admin_user, discord.Member)

    category = await create_category(guild, admin_user, config.GAME_CATEGORY)
    assert category is not None

    channel_name = config.LOBBY_CHANNEL
    channel = await create_channel(guild, admin_user, channel_name, category_name=config.GAME_CATEGORY, is_public=True)
    assert channel is not None
    assert isinstance(channel, discord.TextChannel)

    channel_name = config.WEREWOLF_CHANNEL
    channel = await create_channel(guild, admin_user, channel_name, category_name=config.GAME_CATEGORY, is_public=False)
    assert channel is not None

    # TEST add/remove user to/from channel
    await add_user_to_channel(guild, public_user, channel_name)
    await asyncio.sleep(2)
    assert isinstance(discord.utils.get(channel.members, name=public_user.name), discord.Member)
    await asyncio.sleep(5)
    await remove_user_from_channel(guild, public_user, channel_name)
    await asyncio.sleep(5)
    assert discord.utils.get(channel.members, name=public_user.name) is None

    # TEST send message to private/public channel
    await send_text_to_channel(guild, "Test sending message in public channel", config.LOBBY_CHANNEL)
    await send_text_to_channel(guild, "Test sending message in private channel", config.WEREWOLF_CHANNEL)

    await delete_channel(guild, admin_user, config.WEREWOLF_CHANNEL)
    print("-- End testing admin command --")