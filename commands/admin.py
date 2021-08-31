from discord.utils import get


PRIVATE_CHANNEL_PREFIX='Private_'

def isAdmin(author):
    # Check if this user has 'Admin' right
    admin_role = get(author.guild.roles, name="Admin")
    if admin_role in author.roles:
        return True
    else:
        return False
        
async def create_channel(author, channel_name):
    guild = author.guild
    admin_role = get(guild.roles, name="Admin")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        admin_role: discord.PermissionOverwrite(read_messages=True)
    }
    print("{} created channel {}".format(author.name, channel_name))
    await client.reply("testing")
    return await guild.create_text_channel(channel_name, overwrites=overwrites)

async def delete_channel(author, channel_name):
    try:
        channel = get(author.guild.channels, name=channel_name)
        print("{} deleted channel {}", author.name, channel_name)
        await channel.delete()
    except Exception as e:
        print(e)
        await asyncio.sleep(0)
    


