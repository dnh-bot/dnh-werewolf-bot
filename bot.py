import discord

from game import game,roles
import commands

client = discord.Client()

@client.event
async def on_ready():
    ''' Log ready message, check server roles/channels setup '''
    pass


@client.event
async def on_message(message):
    if verify_ok(message.author):
        commands.parse(client, message) # loop through all commands and do action on first command that match


