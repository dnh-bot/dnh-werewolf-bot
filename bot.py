
import discord
import os
from game import game,roles
from commands import command
from dotenv import load_dotenv

load_dotenv()
# ============ Configurations ===========
# DISCORD_TOKEN in .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX ='!'

if not DISCORD_TOKEN:
    print("Use must setup DISCORD_TOKEN in .env file")
    exit(1)
# ============ Local functions ============

async def process_message(client, message):
    if message.content.strip().startswith(BOT_PREFIX):
        await command.parse_command(client, message)

def verify_ok(user):
    # TODO : Check valid user in valid channel
    return True
# ============ Discord server ============
client = discord.Client()

@client.event
async def on_ready():
    ''' Log ready message, check server roles/channels setup '''
    print("=========================BOT STARTUP=========================")
    for guild in client.guilds:
        print("Connected to server: ",guild.name)



@client.event
async def on_message(message):
    # Check valid author
    if verify_ok(message.author):
        await process_message(client, message) # loop through all commands and do action on first command that match


client.run(DISCORD_TOKEN)

