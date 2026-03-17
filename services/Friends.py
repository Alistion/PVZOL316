# services/Friends.py
from dal import get_all_users

class FriendService:
    @staticmethod
    def get_recommend_list(current_username):
        """获取真实的推荐好友列表"""
        all_users = get_all_users()
        recommend_data = []
        
        for u in all_users:
            # 1. 排除掉当前正在登录的你自己 (current_user)
            if u['username'] == current_username:
                continue
            
            # 2. 构造符合 Flash 解析要求的数据字典
            recommend_data.append({
                "uid": u['id'] + 100000,
                "name": u['username'],
                "grade": u.get('level', 100),           # 从数据库读取等级
                "face": u.get('avatar', "/pvz/avatar/1.png"), # 读取专属头像
                "charm": 999,
                "vip_grade": 2,
                "vip_etime": 2000000000
            })
            
            # 3. 限制返回数量，防止好友面板塞得太满 (比如展示前 15 个)
            if len(recommend_data) >= 3:
                break
            
        return recommend_data

    @staticmethod
    def add_friend(current_username, target_uid):
        # 暂时保持简单成功返回
        return True