import config
from game import roles
import commands


def generate_usage_text_list(cmd, **kwargs):
    if cmd in ("vote", "kill", "guard", "seer", "reborn"):
        player_id = kwargs.get("player_id1", "player_id")
        return [f"`{config.BOT_PREFIX}{cmd} {player_id}`", f"`{config.BOT_PREFIX}{cmd} @user`"]
    elif cmd == "ship":
        player_id1 = kwargs.get("player_id1", "player_id1")
        player_id2 = kwargs.get("player_id2", "player_id2")
        return [f"`{config.BOT_PREFIX}{cmd} {player_id1} {player_id2}`", f"`{config.BOT_PREFIX}{cmd} @user1 @user2`"]
    elif cmd == "timer":
        """Usage: 
        `!timer 60 30 20` -> dayphase=60s, nightphase=30s, alertperiod=20s
        """
        dayphase = kwargs.get("dayphase", "dayphase")
        nightphase = kwargs.get("nightphase", "nightphase")
        alertperiod = kwargs.get("alertperiod", "alertperiod")
        return [f"`{config.BOT_PREFIX}{cmd} {dayphase} {nightphase} {alertperiod}`"]
    else:
        return [f"`{config.BOT_PREFIX}{cmd}`"]


def get_usage_text(cmd):
    return " hoặc ".join(generate_usage_text_list(cmd))


def get_full_cmd_description(cmd):
    return commands.get_command_description(cmd) + f" Sử dụng command {get_usage_text(cmd)}."


def generate_join_text(user, joined_players):
    return f"Người chơi {user} đã tham gia ván đấu. Hiện có {joined_players} người chơi."


def generate_leave_text(user, joined_players):
    return f"Người chơi {user} đã rời ván đấu. Hiện có {joined_players} người chơi."


def generate_too_quick(time_point, last_nextcmd_time):
    return f"Run `{config.BOT_PREFIX}next` command too quick, " + \
        f"please wait for {config.NEXT_CMD_DELAY - time_point + last_nextcmd_time:.1f} seconds"


def generate_start_text():
    return "Tất cả người chơi đã sẵn sàng. Hệ thống tiến hành phân vai và trò chơi sẽ bắt đầu ngay sau đây!"


def generate_end_text():
    return "Trò chơi đã kết thúc."


def generate_role_list_text(roles_data):
    return f"Danh sách nhân vật trong game: {roles_data}"


def generate_execution_text(voted_user, highest_vote_number):
    if highest_vote_number > 0:
        return "Thời gian quyết định đã hết. " +\
            f"Người chơi {voted_user} đã bị đưa lên máy chém với số phiếu bầu là {highest_vote_number}. " +\
            "Hy vọng tình thế của làng có thể thay đổi sau quyết định này.\n" +\
            "===========================================================================\n"
    else:
        return "Không có ai bị hành hình. Trò chơi sẽ tiếp tục. Hãy cẩn thân để sống sót!\n" +\
            "===========================================================================\n"


def generate_day_phase_beginning_text(day):
    return f"Một ngày mới bắt đầu, mọi người thức giấc. Báo cáo tình hình ngày {day}:\n" +\
        f"- Hãy nhập {get_usage_text('vote')} để bỏ phiếu cho người bạn nghi là Sói!\n" +\
        f"- Nhập `{config.BOT_PREFIX}status` để xem trạng thái bỏ phiếu hiện tại."


def generate_night_phase_beginning_text():
    return "Đêm đã tới. Cảnh vật hóa tĩnh lặng, mọi người an giấc. Liệu đêm nay có xảy ra chuyện gì không?"


def generate_player_list_description_text():
    return "Danh sách người chơi hiện tại:\n"


def generate_player_list_embed(player_list, alive_status):
    ids = []
    username_list = []
    for row_id, user in enumerate(player_list, 1):
        ids.append(str(row_id))
        username_list.append(f"<@{user.player_id}>")
    if username_list:
        id_player_list = [f"{i} -> {p}" for i, p in zip(ids, username_list)]
        embed_data = {
            "title": f"{alive_status} player list",
            "description": "Please select a number to vote.",
            "content": [
                ("ID -> Player", id_player_list)
            ]
        }
        return embed_data
    return None


def generate_werewolf_list(werewolf_list):
    werewolf_str = ",".join([f"<@{_id}>" for _id in werewolf_list])
    return f"Danh sách Sói: {werewolf_str}"


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


def generate_after_voting_seer(user, seer_seen_as_werewolf):
    seer_seen_as_werewolf_text = "" if seer_seen_as_werewolf else "không phải "
    return f"Ồ, {user} {seer_seen_as_werewolf_text}là Sói. Pháp lực đã hết, tiên tri cần đi ngủ để hồi phục năng lượng."


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


# Witch
def generate_before_voting_witch():
    return "Phù thủy muốn cứu ai? Bạn chỉ được dùng kỹ năng này 1 lần.\n" +\
        f"Hãy làm phép bằng cách nhập `{config.BOT_PREFIX}reborn ID` cứu người đó."


def generate_after_witch_reborn(user):
    return f"Bạn đã phục sinh thành công {user}"


# Cupid
def generate_start_game_cupid():
    return "Cupid muốn cho cặp đôi nào được đồng sinh cộng tử.\n" +\
        f"Hay làm phép bằng cách nhập `{config.BOT_PREFIX}ship ID1 ID2` để ghép đôi."


def generate_shipped_with(user):
    return f"Bạn và {user} đã được thần tình yêu chọn làm cặp đôi đồng sinh cộng tử."


def generate_after_cupid_ship(user1, user2):
    return f"Bạn đã ghép đôi thành công {user1} và {user2}."


def generate_couple_died(died_player, follow_player, on_day=True):
    if on_day:
        return f"Do {died_player} đã chết nên {follow_player} cũng đã treo cổ tự vẫn đi theo tình yêu của đời mình.\n" +\
            "===========================================================================\n"
    return f"{follow_player} đã dừng cuộc chơi và bước trên con đường tìm kiếm {died_player}.\n" +\
        "===========================================================================\n"


# Common
def generate_out_of_mana():
    return f"Bạn chỉ sử dụng kỹ năng được 1 lần mỗi đêm!"


def generate_out_of_power():
    return f"Bạn chỉ sử dụng kỹ năng được 1 lần duy nhất!"


def generate_invalid_player_alive(user):
    return f"{user} còn sống mà bạn!"


def generate_killed_text(user):
    if user:
        return f"Đêm qua, {user} đã bị mất tích một cách bí ẩn.\n" +\
            "===========================================================================\n"
    else:
        return f"Đêm qua, mọi người đều bình an.\n" +\
            "===========================================================================\n"


def generate_after_death(user):
    return f"Chào mừng {user} đến với nghĩa trang vui vẻ ^^"


def generate_after_reborn(user):
    return f"Chào mừng {user} đã trở lại cuộc đời! Hãy trân trọng cơ hội thứ 2 này!"


def generate_lynch_text(user):
    return f"Dân làng đã đồng lòng loại bỏ {user} khỏi làng"


def generate_dead_target_text():
    return "Người ta đã hẹo rồi, đừng có vote nữa. Vote người nào còn sống thôi :3"


def generate_nobody_voted_text():
    return "Vẫn chưa có ai vote cả :("


def generate_invalid_channel_text(channel):
    # f"Command {config.BOT_PREFIX}{command} only available in {channel}"
    return f"Xài sai chỗ rồi bạn ơi :( Xài trong channel {channel} ấy"


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
    # return "Game already started. Please wait until end game!"
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
    if command in ("kill", "guard", "seer", "vote", "reborn", "ship"):
        usage_text = "\n".join(generate_usage_text_list(command))
        return f"Invalid command.\nUsage:\n{usage_text}"
    elif command in ["fjoin", "fleave"]:
        return f"Invalid command.\nUsage: `{config.BOT_PREFIX}{command} @user1 @user2 ...`"
    else:
        return "Invalid command."


def generate_not_vote_1_player_text():
    return "Đừng có tham vậy chớ! Chỉ được chọn 1 người duy nhất thôi!"


def generate_not_vote_n_player_text(num):
    return f"Bạn phải chọn {num} người chơi để thực hiện command."


def generate_timer_start_text():
    return "Timer start!"


def generate_timer_stop_text():
    return "Timer stopped!"


def generate_timer_remaining_text(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_text = []
    if days > 0:
        time_text.append(f"{days} ngày")
    if hours > 0:
        time_text.append(f"{hours} giờ")
    if minutes > 0:
        time_text.append(f"{minutes} phút")
    if seconds > 0 or days == hours == minutes == seconds == 0:
        time_text.append(f"{seconds} giây")

    return f"🔔 Bing boong! Còn {' '.join(time_text)}..."


def generate_timer_up_text():
    return f"⏰ HẾT GIỜ!!!!"


def generate_help_command_text(command=None):
    # TODO: read info from command_info.json file
    help_embed_data = {
        "title": "Werewolf Bot Help",
        "description": f"Full command list. You can get more information on a command using `{config.BOT_PREFIX}help cmd <name of command>`",
        "content": []
    }
    command = command.lower() if isinstance(command, str) else command
    if command is None:
        help_embed_data["color"] = 0xffffff
        help_embed_data["content"] = [("All commands", [" | ".join(f"`{cmd}`" for cmd in commands.get_all_commands())])]
        # TODO: cmd_description + (Dành cho tất cả mọi người.|Dành riêng cho {role}.)
    else:
        command_description = commands.get_command_description(command)
        if command_description is not None:
            help_embed_data["color"] = 0x17a168
            help_embed_data["title"] += f" for command `{command}`"
            help_embed_data["description"] = command_description

            usage_str = ["- " + usage_text for usage_text in generate_usage_text_list(command)]
            help_embed_data["content"] = [("Usage", usage_str)]

            if command in ("vote", "kill", "guard", "seer", "reborn", "ship"):
                help_embed_data["content"].append(
                    ("Example", ["- " + usage_text for usage_text in generate_usage_text_list(command, player_id1=2, player_id2=3)])
                )
        else:
            help_embed_data["color"] = 0xdc4e4e
            help_embed_data["title"] = f"Invalid help for command `{command}`"
            help_embed_data["description"] = "A command with this name doesn't exist"

    return help_embed_data


def generate_help_role_text(role=None):
    help_embed_data = {
        "title": "Werewolf Bot Help",
        "description": f"Full role list. You can get more information on a role using `{config.BOT_PREFIX}help role <name of role>`",
        "content": []
    }
    all_roles_name = [a_role.__name__ for a_role in roles.get_all_roles()]
    role = role.capitalize() if isinstance(role, str) else role
    if role is None:
        help_embed_data["color"] = 0xffffff
        for a_role in roles.get_all_roles():
            name_in_this_language = roles.get_role_name_in_language(a_role.__name__, config.TEXT_LANGUAGE)
            if name_in_this_language:
                title = a_role.__name__ + " - " + name_in_this_language
            else:
                title = a_role.__name__

            help_embed_data["content"].append((title, [roles.get_role_description(a_role.__name__)]))

    elif role in all_roles_name:
        help_embed_data["color"] = 0x3498db
        help_embed_data["title"] += f" for role `{role}`"
        name_in_this_language = roles.get_role_name_in_language(role, config.TEXT_LANGUAGE)
        if name_in_this_language is not None:
            help_embed_data["title"] += f" ({name_in_this_language})"

        help_embed_data["description"] = roles.get_role_description(role)
        nighttime_command = roles.get_role_nighttime_command(role)
        if nighttime_command:
            nighttime_action_description = get_full_cmd_description(nighttime_command)
        else:
            nighttime_action_description = "Chỉ việc đi ngủ thôi :joy:"

        help_embed_data["content"] = [
            ("Ban ngày", [get_full_cmd_description("vote")]),
            ("Ban đêm", [nighttime_action_description]),
        ]
    else:
        help_embed_data["color"] = 0xdc4e4e
        help_embed_data["title"] = f"Invalid help for role `{role}`"
        help_embed_data["description"] = "A role with this name doesn't exist"

    return help_embed_data


def generate_help_text(*args):
    if len(args) == 0:
        help_embed_data = {
            "color": 0xffffff,
            "title": "Werewolf Bot Help",
            "description": "Full list of things. You can get more information on " +\
                           f"a command using `{config.BOT_PREFIX}help cmd <name of command>` or " +\
                           f"a role using `{config.BOT_PREFIX}help role <name of role>`",
            "content": [
                ("All commands", [" | ".join(f"`{cmd}`" for cmd in commands.get_all_commands())]),
                ("All roles", [" | ".join(f"`{a_role.__name__}`" for a_role in roles.get_all_roles())])
            ]
        }
    elif args[0] == "role":
        help_embed_data = generate_help_role_text(None if len(args) == 1 else args[1])
    elif args[0] == "cmd":
        help_embed_data = generate_help_command_text(None if len(args) == 1 else args[1])
    else:
        help_embed_data = {
            "color": 0xdc4e4e,
            "title": "Invalid help argument",
            "description": f"Argument with name `{args[0]}` doesn't exist. Please type `{config.BOT_PREFIX}help`.",
            "content": []
        }

    return help_embed_data


def generate_table(header, data):
    # This needs to be adjusted based on expected range of values or calculated dynamically
    for i in data:
        header.append("   ".join([str(item) for item in data]))

    # Joining up scores into a line
    return "```"+"\n".join(header) + "```"
