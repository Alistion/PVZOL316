# services/Friends.py
from dal import get_all_users,add_friend_to_db, get_friend_details

class FriendService:
    @staticmethod
    def get_recommend_list(current_username):
        """获取真实的推荐好友列表（已修复：排除已有好友）"""
        all_users = get_all_users()
        
        # 1. 【新增】获取当前玩家已经添加的好友列表
        my_friends = get_friend_details(current_username)
        
        # 2. 【新增】提取出所有已有好友的 username，存进一个集合(Set)里方便快速比对
        my_friend_usernames = {f['username'] for f in my_friends}
        
        recommend_data = []
        
        for u in all_users:
            # 3. 排除掉当前正在登录的你自己
            if u['username'] == current_username:
                continue
            
            # 4. 如果这个人已经在我的好友列表里了，直接跳过！
            if u['username'] in my_friend_usernames:
                continue
            
            # 5. 构造符合 Flash 解析要求的数据字典
            recommend_data.append({
                "uid": u['id'] + 100000,
                "name": u['username'],
                "grade": u.get('level', 100),           
                "face": u.get('avatar', "/pvz/avatar/1.png"), 
                "charm": 999,
                "vip_grade": 2,
                "vip_etime": 2000000000
            })
            
            # 6. 限制返回数量，防止好友面板塞得太满 (比如展示前 15 个)
            if len(recommend_data) >= 3:
                break
            
        return recommend_data
    @staticmethod
    def get_my_friends(current_username):
        """获取我的真实好友列表 (供游戏主界面渲染)"""
        friends_data = get_friend_details(current_username)
        res = []
        for f in friends_data:
            res.append({
                "uid": f['id'] + 100000, "name": f['username'],
                "grade": f.get('level', 100), "face": f.get('avatar', "/pvz/avatar/1.png"),
                "charm": 888, "vip_grade": 1, "vip_etime": 2000000000
            })
        return res
    @staticmethod
    def add_friend(current_username, target_uid):
        """执行添加好友动作"""
        if target_uid:
            add_friend_to_db(current_username, int(target_uid))
            print(f"[好友系统] {current_username} 成功添加了 UID: {target_uid} 为好友！")
    
    