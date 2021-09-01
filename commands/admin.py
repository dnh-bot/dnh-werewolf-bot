import discord
from discord.utils import get
from utils import logger
import asyncio

PRIVATE_CHANNEL_PREFIX='Private_'

def isAdmin(author):
    # Check if this user has 'Admin' right
    admin_role = get(author.guild.roles, name="Admin")
    if admin_role in author.guild.roles:
        return True
    else:
        return False
        
async def create_channel(author, channel_name):
    # Create text channel with limited permissions
    # Only the author and Admin roles can view this channel
    guild = author.guild
    existing_channel = get(guild.channels, name=channel_name)
    if not existing_channel:
        admin_role = get(guild.roles, name="Admin")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            admin_role: discord.PermissionOverwrite(read_messages=True)
        }
        response = "{} created channel {}".format(author.name, channel_name)
        print(response)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        await channel.send(response)
        return channel

async def delete_channel(author, channel_name):
    # Delete text channel. Any Admin can delete it
    try:
        channel = get(author.guild.channels, name=channel_name)
        response = "{} deleted channel {}".format(author.name, channel_name)
        print(response)
        await channel.send(response)
        await channel.delete()
    except Exception as e:
        print(e)
        await asyncio.sleep(0)

async def add_player_to_channel(guild, player, channel_name):
    # Add a player to specific channel
    print("===", player, channel_name)
    channel = get(guild.channels, name=channel_name)
    await channel.set_permissions(player, read_messages=True, send_messages=True)