"""
This provides APIs for Admin role and bot role
"""

import asyncio

import discord

import categories
from utils import logger, common
import config


def is_valid_category(message, game):
    try:  # Channel may not belong to any category, make message.channel.category empty
        return message.channel.category.id == game.get_category().id
    except Exception as e:  # Command not in Category channel
        print(e)
        return False


USER_LIST = common.read_json_file("json/user_info.json")


def is_admin(author):
    # Check if this user has "Admin" right
    return str(author.id) in USER_LIST["dev"] or str(author.id) in USER_LIST["admin"] \
        or discord.utils.get(author.roles, name=config.ADMIN_ROLE) is not None


def list_users(guild):
    print("Server member: ")
    for user in guild.members:
        print("-", user.display_name, user.id)
    print("-------------")


async def create_category(guild, author, category_name):
    # Create a category with limited permissions
    # Only the author and Admin roles can view this category
    print("Try creating category_name=", category_name)
    existing_category = discord.utils.get(guild.categories, name=category_name)
    if not existing_category:
        try:
            admin_role = discord.utils.get(guild.roles, name=config.ADMIN_ROLE)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            response = f"{author.name} created category {category_name}"
            print(response)
            category = await guild.create_category(category_name, overwrites=overwrites)
            return category
        except Exception as e:
            print("Exception at #", category_name, author)
            logger.logger_debug(guild.categories)
            print(e)

    response = f"Category {category_name} exists"
    print(response)
    return existing_category

async def delete_category(guild, author, category_name):
    # Delete category. Any Admin can delete it
    try:
        category = discord.utils.get(guild.categories, name=category_name)
        assert isinstance(category, discord.CategoryChannel)
        response = f"{author.display_name} deleted category {category_name}"
        print(response)
        await category.delete()
        return True
    except Exception as e:
        print("Exception at #", category_name, author)
        logger.logger_debug(guild.categories)
        print(e)


def get_channel_in_category(category, channel_name):
    return discord.utils.get(category.channels, name=channel_name)


async def create_channel(category, author, channel_name, is_public=False, is_admin_writeonly=False):
    # Create text channel with limited permissions
    # Only the author and Admin roles can view this channel
    existing_channel = get_channel_in_category(category, channel_name)
    if not existing_channel:
        try:
            admin_role = discord.utils.get(category.guild.roles, name=config.ADMIN_ROLE)
            overwrites = {
                category.guild.default_role: discord.PermissionOverwrite(read_messages=is_public, send_messages=is_public and not is_admin_writeonly),
                category.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=not is_admin_writeonly),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            response = f"{author.name} created channel {channel_name}"
            print(response)
            # logger.logger_debug(category)
            channel = await category.create_text_channel(channel_name, overwrites=overwrites)
            await channel.send(response)
            return channel
        except Exception as e:
            print("Exception at #", channel_name, author)
            logger.logger_debug(category.channels)
            print(e)

    response = f"Channel {channel_name} exists"
    print(response)
    return existing_channel


async def delete_channel(category, author, channel_name):
    # Delete text channel. Any Admin can delete it
    try:
        channel = get_channel_in_category(category, channel_name)
        response = f"{author.display_name} deleted channel {channel_name}"
        assert isinstance(channel, discord.TextChannel)
        print(response)
        # await channel.send(response)
        await channel.delete()
        return True
    except Exception as e:
        print("Exception at #", channel_name, author)
        logger.logger_debug(category.channels)
        print(e)


async def add_user_to_channel(category, user, channel_name, is_read=True, is_send=True):
    # Add a user to specific channel
    channel = get_channel_in_category(category, channel_name)
    if not channel:
        await asyncio.sleep(1)  # Wait 1s here to wait for channel is ready
        channel = get_channel_in_category(category, channel_name)
    try:
        await channel.set_permissions(user, read_messages=is_read, send_messages=is_send, add_reactions=is_send)
        # await channel.set_permissions(user, create_public_threads=is_send, create_private_threads=False)  # discord.py >= 2.0
        print(f"Successfully added {user} to {channel_name} read={is_read} send={is_send}")
        return True
    except Exception as e:
        print(f"Failed to add {user} into #{channel_name}, {is_read} {is_send}")
        logger.logger_debug(category.channels)
        print("add_user_to_channel:", e)


async def remove_user_from_channel(category, user, channel_name):
    # Add a user to specific channel
    print("===", user, channel_name)
    channel = get_channel_in_category(category, channel_name)
    try:
        await channel.set_permissions(user, read_messages=False, send_messages=False, add_reactions=False)
        # await channel.set_permissions(user, create_public_threads=False, create_private_threads=False)  # discord.py >= 2.0
        print("Successfully removed ", user, " from ", channel_name)
        return True
    except Exception as e:
        print(e)


async def send_text_to_channel(category, text, channel_name):
    """ Send a message to a channel """
    channel = get_channel_in_category(category, channel_name)
    if channel is None:
        print(f"Channel #{channel_name} in category {category.name} does not exist!")
        return False

    try:
        await channel.send(text)
        return True
    except Exception as e:
        print("send_text_to_channel:", e)

    return False


async def send_embed_to_channel(category, embed_data, channel_name, *_):
    """Send an embed message to a channel"""

    channel = get_channel_in_category(category, channel_name)
    print(channel, embed_data)
    try:
        color = embed_data["color"] if "color" in embed_data else 0
        embed = discord.Embed(title=embed_data["title"], description=embed_data.get("description"), color=color)
        for field_name, field_value in embed_data["content"]:
            field_value_str = "\n".join(field_value).rstrip()
            if field_name and field_value_str:
                embed.add_field(name=field_name, value=field_value_str, inline=False)

        await channel.send(embed=embed)
        return True
    except Exception as e:
        print("send_embed_to_channel:", e)


async def delete_all_personal_channel(category):
    if category:
        personal_channels = [c for c in category.channels if c.name.startswith(config.PERSONAL)]
        await asyncio.gather(*[c.delete() for c in personal_channels])


async def create_game_category(guild, client_user, category_name):
    """Create GAME_CATEGORY if not existing"""
    category = await create_category(guild, client_user, category_name)
    if not category:
        return
    category_config = categories.CategoryConfig(category_name)
    await create_channel(category, client_user, category_config.LOBBY_CHANNEL, is_public=True)
    await create_channel(category, client_user, category_config.GAMEPLAY_CHANNEL, is_public=False)
    await create_channel(category, client_user, category_config.LEADERBOARD_CHANNEL, is_public=True, is_admin_writeonly=True)


async def clean_game_category(guild, client_user, category_name, is_deleting_category=False):
    """Clean GAME_CATEGORY"""
    category = discord.utils.get(guild.categories, name=category_name)
    print(category)
    if not category:
        return
    category_config = categories.CategoryConfig(category_name)
    try:
        await delete_channel(category, client_user, category_config.GAMEPLAY_CHANNEL)
        await delete_channel(category, client_user, category_config.WEREWOLF_CHANNEL)
        await delete_channel(category, client_user, category_config.CEMETERY_CHANNEL)
        await delete_channel(category, client_user, category_config.COUPLE_CHANNEL)
        await delete_all_personal_channel(category)

        if is_deleting_category:
            # Comment this to keep the board
            await delete_channel(category, client_user, category_config.LEADERBOARD_CHANNEL)
            await delete_channel(category, client_user, category_config.LOBBY_CHANNEL)
            await delete_category(guild, client_user, category_name)
        else:
            await create_channel(category, client_user, category_config.GAMEPLAY_CHANNEL, is_public=False)

    except Exception as e:
        print(e)


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
    category_config = categories.CategoryConfig()

    channel_name = category_config.LOBBY_CHANNEL
    channel = await create_channel(category, admin_user, channel_name, is_public=True)
    assert channel is not None
    assert isinstance(channel, discord.TextChannel)

    channel_name = category_config.WEREWOLF_CHANNEL
    channel = await create_channel(category, admin_user, channel_name, is_public=False)
    assert channel is not None

    # TEST add/remove user to/from channel
    await add_user_to_channel(category, public_user, channel_name, is_read=True, is_send=True)
    await asyncio.sleep(2)
    assert isinstance(discord.utils.get(channel.members, name=public_user.name), discord.Member)
    await asyncio.sleep(5)
    await remove_user_from_channel(category, public_user, channel_name)
    await asyncio.sleep(5)
    assert discord.utils.get(channel.members, name=public_user.name) is None

    # TEST send message to private/public channel
    await send_text_to_channel(category, "Test sending message in public channel", category_config.LOBBY_CHANNEL)
    await send_text_to_channel(category, "Test sending message in private channel", category_config.WEREWOLF_CHANNEL)

    await delete_channel(category, admin_user, category_config.WEREWOLF_CHANNEL)
    print("-- End testing admin command --")
