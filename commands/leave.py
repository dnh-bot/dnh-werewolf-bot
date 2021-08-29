from game import game

@cmd(....)
async def do_leave(client, message):
    ''' Verify author '''
    author = message.author
    game.remove_player(author)
    client.reply("Goodbye player {}".format(author)

