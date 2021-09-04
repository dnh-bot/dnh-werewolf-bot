import config


def generate_join_text(user):
    return f"Người chơi {user} đã tham gia ván đấu."


def generate_start_text():
    return "Tất cả người chơi đã sẵn sàng. Hệ thống tiến hành phân vai và trò chơi sẽ bắt đầu ngay sau đây!"


def generate_vote_user_text(voted_user, users_list, user_vote_number_list):
    return f"""Đã vote hành hình {voted_user}.\nDanh sách những kẻ có khả năng bị hành hình:""" +\
        "".join(
            f"\n- {user}: {user_vote_number} số phiếu."
            for user, user_vote_number in zip(users_list, user_vote_number_list)
        )


def generate_execution_text(users_list, user_vote_number_list):
    highest_vote_number = max(user_vote_number_list)
    if user_vote_number_list.count(highest_vote_number) == 1:
        voted_user = [
            user
            for user, user_vote_number in zip(users_list, user_vote_number_list)
            if user_vote_number == highest_vote_number
        ][0]
        return "Thời gian quyết định đã hết. " +\
            f"Người chơi {voted_user} đã bị đưa lên máy chém với số phiếu bầu là {highest_vote_number}. " +\
            "Hy vọng tình thế của làng có thể thay đôi sau quyết định này."
    else:
        return "Không có ai bị hành hình. Trò chơi sẽ tiếp tục. Hãy cẩn thân để sống sót!"


def generate_day_phase_beginning_text(day, role_member_alive):
    result = f"Một ngày mới bắt đầu, mọi người thức giấc. Báo cáo tình hình ngày {day}:\n- Các người chơi hiện tại: {role_member_alive}."
    return result


def generate_night_phase_beginning_text():
    return "Đêm đã tới. Cảnh vật hóa tĩnh lặng, mọi người an giấc. Liệu đêm nay có xảy ra chuyện gì không?"


def generate_before_voting_werewolf():
    return f"Đêm nay, Sói muốn lấy mạng ai? Hãy nhập {config.BOT_PREFIX}choose user để lặng lẽ xử lý nạn nhân. " +\
        "Các Werewolf hãy chọn đúng để giành lấy chiến thắng!"


def generate_after_voting_werewolf(user):
    return f"Đang tiến hành xử lý {user}. Mong là mọi việc thuận lợi, đi ngủ thôi."


def generate_before_voting_seer():
    return "Tiên tri muốn thấy gì, từ ai? " +\
        f"Hãy làm phép bằng cách nhập {config.BOT_PREFIX}choose user để xem người chơi đó là ai."


def generate_after_voting_seer(user, is_werewolf):
    is_werewolf_text = "" if is_werewolf else "không phải "
    return f"Ồ, {user} {is_werewolf_text}là sói. Pháp lực đã hết, tiên tri cần đi ngủ để hồi phục năng lượng."


def generate_before_voting_guard():
    return f"Bảo vệ muốn ai sống qua đêm nay, hãy nhập {config.BOT_PREFIX}choose user để người đó qua đêm an bình. " +\
        "Nhớ chú ý an toàn của bản thân!"


def generate_after_voting_guard(user):
    return f"Đã bảo vệ thành công {user}"

def generate_killed_text(user):
    return f"Đêm qua, {user} đã bị mất tích một cách bí ẩn"

def generate_lynch_text(user):
    return f"Dân làng đã đồng lòng loại bỏ {user} khỏi làng"

def generate_endgame_text(winner):
    return f"Trò chơi kết thúc, với chiến thắng thuộc về phe {winner}"
