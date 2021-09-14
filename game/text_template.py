import config


def generate_join_text(user, joined_players):
    return f"Người chơi {user} đã tham gia ván đấu. Hiện có {joined_players} người chơi."


def generate_leave_text(user, joined_players):
    return f"Người chơi {user} đã rời ván đấu. Hiện có {joined_players} người chơi."


def generate_too_quick(time_point, last_nextcmd_time):
    return f"Run `{config.BOT_PREFIX}next` command too quick, " + \
        f"please wait for {config.NEXT_CMD_DELAY - time_point + last_nextcmd_time:.1f} seconds"


def generate_start_text():
    return "Tất cả người chơi đã sẵn sàng. Hệ thống tiến hành phân vai và trò chơi sẽ bắt đầu ngay sau đây!"


def generate_role_list_text(roles):
    return f"Danh sách nhân vật trong game: {roles}"


def generate_execution_text(voted_user, highest_vote_number):
    if highest_vote_number > 0:
        return "Thời gian quyết định đã hết. " +\
            f"Người chơi {voted_user} đã bị đưa lên máy chém với số phiếu bầu là {highest_vote_number}. " +\
            "Hy vọng tình thế của làng có thể thay đổi sau quyết định này.\n" +\
            "==========================================================================="
    else:
        return "Không có ai bị hành hình. Trò chơi sẽ tiếp tục. Hãy cẩn thân để sống sót!\n" +\
            "==========================================================================="


def generate_day_phase_beginning_text(day):
    return f"Một ngày mới bắt đầu, mọi người thức giấc. Báo cáo tình hình ngày {day}:\n" +\
        f"- Hãy nhập `{config.BOT_PREFIX}vote ID` hoặc `{config.BOT_PREFIX}vote @user` để bỏ phiếu cho người bạn nghi là Sói!\n" +\
        f"- Nhập `{config.BOT_PREFIX}status` để xem trạng thái bỏ phiếu hiện tại."


def generate_night_phase_beginning_text():
    return "Đêm đã tới. Cảnh vật hóa tĩnh lặng, mọi người an giấc. Liệu đêm nay có xảy ra chuyện gì không?"


def generate_player_list_description_text():
    return "Danh sách người chơi hiện tại:\n"


def generate_player_list_embed(alive_player_list):
    ids = []
    alive_players = []
    for row_id, user in enumerate(alive_player_list, 1):
        ids.append(str(row_id))
        alive_players.append(f"<@{user.player_id}>")
    if alive_players:
        id_player_list = [f"{i} -> {p}" for i, p in zip(ids, alive_players)]
        embed_data = {
            "title": "Player list",
            "description": "Please select a number to vote.",
            "content": [
                ("ID -> Player", id_player_list)
            ]
        }
        return embed_data
    return None


def generate_before_voting_werewolf():
    return f"Đêm nay, Sói muốn lấy mạng ai? Hãy nhập `{config.BOT_PREFIX}kill ID` để lặng lẽ xử lý nạn nhân.\n" +\
        f"Ví dụ: `{config.BOT_PREFIX}kill 2`\n"


def generate_after_voting_werewolf(user):
    return f"Đang tiến hành xử lý {user}. Mong là mọi việc thuận lợi, đi ngủ thôi."


def generate_vote_text(author, user):
    return f"{author} đã biểu quyết loại bỏ {user} khỏi làng"


def generate_vote_for_game_text(command, author, text):
    return f"Player {author} votes for {command} game. {text}"


def generate_kill_text(werewolf, user):
    return f"Sói {werewolf} muốn xử lý {user} trong đêm nay"


def generate_before_voting_seer():
    return "Tiên tri muốn thấy gì, từ ai? " +\
        f"Hãy làm phép bằng cách nhập `{config.BOT_PREFIX}seer ID` để xem người chơi đó là ai."


def generate_after_voting_seer(user, is_werewolf):
    is_werewolf_text = "" if is_werewolf else "không phải "
    return f"Ồ, {user} {is_werewolf_text}là Sói. Pháp lực đã hết, tiên tri cần đi ngủ để hồi phục năng lượng."


# Guard
def generate_before_voting_guard():
    return f"Bảo vệ muốn ai sống qua đêm nay, hãy nhập `{config.BOT_PREFIX}guard ID` để người đó qua đêm an bình.\n" +\
        f"Ví dụ: `{config.BOT_PREFIX}guard 2`\n" +\
        "Bạn chỉ sử dụng kỹ năng được 1 lần mỗi đêm. Hãy cẩn trọng!"


def generate_after_voting_guard(user):
    return f"Đã bảo vệ thành công {user}"


def generate_invalid_guard_selfprotection():
    return f"Ai lại chơi tự bảo vệ mình :rage:"


def generate_invalid_guard_yesterdaytarget():
    return f"Hôm qua bạn đã bảo vệ người này. Hãy đổi mục tiêu khác hôm nay!"


# Common
def generate_out_of_mana():
    return f"Bạn chỉ sử dụng kỹ năng được 1 lần mỗi đêm!"


def generate_killed_text(user):
    if user:
        return f"Đêm qua, {user} đã bị mất tích một cách bí ẩn.\n" +\
            "==========================================================================="
    else:
        return f"Đêm qua, mọi người đều bình an.\n" +\
            "==========================================================================="


def generate_lynch_text(user):
    return f"Dân làng đã đồng lòng loại bỏ {user} khỏi làng"


def generate_dead_target_text():
    return "Người ta đã hẹo rồi, đừng có vote nữa. Vote người nào còn sống thôi :3"


def generate_nobody_voted_text():
    return "Vẫn chưa có ai vote cả :("


def generate_invalid_channel_text(channel):
    # f"Command {config.BOT_PREFIX}{command} only available in {channel}"
    return f"Xài sai chỗ rồi bạn ơi :( Xài trong channel {channel} ấy",


def generate_invalid_target():
    return f"Dùng kỹ năng đến đúng người bạn êy!"


def generate_invalid_author():
    return f"Hiện tại bạn không được phép dùng kỹ năng này!"


def generate_invalid_nighttime():
    return f"Ráng đợi tới đêm bạn êy!"


def generate_game_started_text():
    # return f"Game started in #{config.GAMEPLAY_CHANNEL}! (Only Player can view)"
    return f"Trò chơi đã bắt đầu ở #{config.GAMEPLAY_CHANNEL}!"


def generate_game_not_started_text():
    # return "Game has not started yet!"
    return f"Trò chơi chưa bắt đầu!"


def generate_game_already_started_text():
    #return "Game already started. Please wait until end game!"
    return f"Trò chơi đã bắt đầu rồi. Xin đợi xíu bạn nha."


def generate_wait_next_game_text():
    return "Tiếc quá, thôi đợi game sau bạn nhé :("


def generate_game_stop_text():
    return "Trò chơi kết thúc!"


def generate_endgame_text(winner):
    return f"Trò chơi kết thúc với chiến thắng thuộc về phe {winner}."


def generate_not_in_game_text():
    return "Hiện bạn đang không ở trong game."


def generate_already_in_game_text():
    return "Ơ kìa, bạn đã vào game rồi mà :v"


def generate_invalid_command_text(command):
    if command in ["kill", "guard", "seer", "vote"]:
        return f"Invalid command.\nUsage: `{config.BOT_PREFIX}{command} ID`"
    elif command in ["fjoin", "fleave"]:
        return f"Invalid command.\nUsage: `{config.BOT_PREFIX}{command} @user1 @user2 ...`"
    else:
        return "Invalid command."


def generate_not_vote_1_player_text():
    return "Đừng có tham vậy chớ! Chỉ được chọn 1 người duy nhất thôi!"


def generate_timer_start_text():
    return "Timer start!"


def generate_timer_stop_text():
    return "Timer stopped!"


def generate_timer_remaining_text(count):
    return f'Bing boong! Còn {count} giây...'


def generate_timer_up_text():
    return f"HẾT GIỜ!!!!"


def generate_table(header, data):
    # This needs to be adjusted based on expected range of values or calculated dynamically
    for i in data:
        header.append('   '.join([str(item) for item in data]))

    # Joining up scores into a line
    return '```'+'\n'.join(header) + '```'
