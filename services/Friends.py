# services/Friends.py
from config import UID_OFFSET
from dal import add_friend_to_db, get_all_users, get_friend_details


class FriendService:
    @staticmethod
    def get_recommend_list(current_username):
        """获取真实的推荐好友列表（排除自己和已有好友）"""
        all_users = get_all_users()

        # 获取已有好友的 username 集合，方便快速比对
        my_friends = get_friend_details(current_username)
        my_friend_usernames = {f["username"] for f in my_friends}

        recommend_data = []
        for u in all_users:
            if u["username"] == current_username:
                continue
            if u["username"] in my_friend_usernames:
                continue

            recommend_data.append(
                {
                    "uid": u["id"] + UID_OFFSET,
                    "name": u["username"],
                    "grade": u.get("level", 100),
                    "face": u.get("avatar", "/pvz/avatar/1.png"),
                    "charm": 999,
                    "vip_grade": 2,
                    "vip_etime": 2000000000,
                }
            )

            if len(recommend_data) >= 3:
                break

        return recommend_data

    @staticmethod
    def get_my_friends(current_username):
        """获取我的真实好友列表（供游戏主界面渲染）"""
        friends_data = get_friend_details(current_username)
        return [
            {
                "uid": f["id"] + UID_OFFSET,
                "name": f["username"],
                "grade": f.get("level", 100),
                "face": f.get("avatar", "/pvz/avatar/1.png"),
                "charm": 888,
                "vip_grade": 1,
                "vip_etime": 2000000000,
            }
            for f in friends_data
        ]

    @staticmethod
    def add_friend(current_username, target_uid):
        """执行添加好友动作"""
        if target_uid:
            add_friend_to_db(current_username, int(target_uid))
            print(f"[好友系统] {current_username} 成功添加了 UID:{target_uid} 为好友！")
