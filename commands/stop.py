from game import game

@cmd(....)
async def do_join(client, message):
    ''' Verify author '''
    author = message.author
    game.stop()
    client.reply("Game stop")

