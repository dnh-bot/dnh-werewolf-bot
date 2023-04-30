"""
This provides APIs for Admin role and bot role
"""

from time import sleep
import discord
import asyncio
from utils import logger
import config


def is_valid_category(message):
    try:  # Channel may not belong to any category, make message.channel.category empty
        return message.channel.category.name == config.GAME_CATEGORY
    except:  # Command not in Category channel
        return False


def is_admin(author):
    # Check if this user has "Admin" right
    return discord.utils.get(author.roles, name="Admin") is not None


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
            admin_role = discord.utils.get(guild.roles, name="Admin")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            response = f"{author.name} created category {category_name}"
            print(response)
            category = await guild.create_category(category_name, overwrites=overwrites)
            await create_channel(guild, author, config.LOBBY_CHANNEL, is_public=True)
            await create_channel(guild, author, config.GAMEPLAY_CHANNEL, is_public=False)
            await create_channel(guild, author, config.LEADERBOARD_CHANNEL, is_public=True, is_admin_writeonly=True)
            return category
        except Exception as e:
            print("Exception at #", category_name, author)
            logger.logger_debug(guild.categories)
            print(e)
    return existing_category


async def delete_category(guild, author, category_name=config.GAME_CATEGORY):
    # Delete category. Any Admin can delete it
    try:
        category = discord.utils.get(guild.categories, name=category_name)
        assert isinstance(category, discord.CategoryChannel)
        response = f"{author.display_name} deleted channel {category_name}"
        print(response)
        await category.delete()
        return True
    except Exception as e:
        print("Exception at #", category_name, author)
        logger.logger_debug(guild.categories)
        print(e)


async def create_channel(guild, author, channel_name, is_public=False, is_admin_writeonly=False):
    # Create text channel with limited permissions
    # Only the author and Admin roles can view this channel
    category = discord.utils.get(guild.categories, name=config.GAME_CATEGORY)
    existing_channel = discord.utils.get(guild.channels, name=channel_name, category=category)
    if not existing_channel:
        try:
            admin_role = discord.utils.get(guild.roles, name="Admin")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=is_public, send_messages=is_public and not is_admin_writeonly),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=not is_admin_writeonly),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            response = "{} created channel {}".format(author.name, channel_name)
            print(response)
            # logger.logger_debug(category)
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
            await channel.send(response)
            return channel
        except Exception as e:
            print("Exception at #", channel_name, author)
            logger.logger_debug(guild.channels)
            print(e)
    return existing_channel


async def delete_channel(guild, author, channel_name):
    # Delete text channel. Any Admin can delete it
    try:
        category = discord.utils.get(guild.categories, name=config.GAME_CATEGORY)
        channel = discord.utils.get(guild.channels, name=channel_name, category=category)
        response = f"{author.display_name} deleted channel {channel_name}"
        assert isinstance(channel, discord.TextChannel)
        print(response)
        # await channel.send(response)
        await channel.delete()
        return True
    except Exception as e:
        print("Exception at #", channel_name, author)
        logger.logger_debug(guild.channels)
        print(e)


async def add_user_to_channel(guild, user, channel_name, is_read=True, is_send=True):
    # Add a user to specific channel
    category = discord.utils.get(guild.categories, name=config.GAME_CATEGORY)
    channel = discord.utils.get(guild.channels, name=channel_name, category=category)
    if not channel:
        await asyncio.sleep(1)  # Wait 1s here to wait for channel is ready
        channel = discord.utils.get(guild.channels, name=channel_name, category=category)
    try:
        await channel.set_permissions(user, read_messages=is_read, send_messages=is_send)
        print(f"Successfully added {user} to {channel_name} read={is_read} send={is_send}")
        return True
    except Exception as e:
        print(f"Failed to add {user} into #{channel_name}, {is_read} {is_send}")
        logger.logger_debug(guild.channels)
        print(e)


async def remove_user_from_channel(guild, user, channel_name):
    # Add a user to specific channel
    print("===", user, channel_name)
    category = discord.utils.get(guild.categories, name=config.GAME_CATEGORY)
    channel = discord.utils.get(guild.channels, name=channel_name, category=category)
    try:
        await channel.set_permissions(user, read_messages=False, send_messages=False)
        print("Successfully removed ", user, " from ", channel_name)
        return True
    except Exception as e:
        print(e)


async def send_text_to_channel(guild, text, channel_name):
    """ Send a message to a channel """
    category = discord.utils.get(guild.categories, name=config.GAME_CATEGORY)
    channel = discord.utils.get(guild.channels, name=channel_name, category=category)
    try:
        await channel.send(text)
        return True
    except Exception as e:
        print(e)


async def send_embed_to_channel(guild, embed_data, channel_name, *args):
    """Send an embed message to a channel"""

    category = discord.utils.get(guild.categories, name=config.GAME_CATEGORY)
    channel = discord.utils.get(guild.channels, name=channel_name, category=category)
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


async def delete_all_personal_channel(guild):
    # TODO: Only delete personal channels under GAME category
    await asyncio.gather(*[c.delete() for c in guild.channels if c.name.startswith("personal")])


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
    channel = await create_channel(guild, admin_user, channel_name, is_public=True)
    assert channel is not None
    assert isinstance(channel, discord.TextChannel)

    channel_name = config.WEREWOLF_CHANNEL
    channel = await create_channel(guild, admin_user, channel_name, is_public=False)
    assert channel is not None

    # TEST add/remove user to/from channel
    await add_user_to_channel(guild, public_user, channel_name, is_read=True, is_send=True)
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
