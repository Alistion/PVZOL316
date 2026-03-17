# services/Arena.py
from dal import get_arena_lineup, update_arena_lineup


class ArenaService:
    @staticmethod
    def get_arena_list(username):
        """
        获取斗技场对手列表面板数据
        彻底匹配 AS3 客户端的 param1 解析逻辑
        """

        lineup_str = get_arena_lineup(username)
        formatted_organisms = []
        if lineup_str:
            for org_id in lineup_str.split(','):
                if org_id.strip():
                    formatted_organisms.append({"id": int(org_id.strip())})
        
        owner_data = {
            "num": 5,        
            "rank": 999,     
            "organisms": formatted_organisms  
        }

        # 2. 对手列表数据 (对应 param1.opponent)
        opponents = [
            {
                "nickname": "全服第一神豪",
                "userid": "10001",
                "platform_user_id": "10001",
                "rank": 1,
                "grade": 150,
                "face": "/pvz/avatar/1.png",
                "vip_grade": 1,
                "vip_etime": 2000000000,
                "organism": [  # 对手的植物阵容
                    
                ]
            },
            {
                "nickname": "疯狂的戴夫",
                "userid": "10002",
                "platform_user_id": "10002",
                "rank": 2,
                "grade": 100,
                "face": "/pvz/avatar/1.png",
                "vip_grade": 3,
                "vip_etime": 2000000000,
                "organism": [
                    
                ]
            },
            {
                "nickname": "僵尸博士",
                "userid": "10003",
                "platform_user_id": "10003",
                "rank": 3,
                "grade": 80,
                "face": "/pvz/avatar/1.png",
                "vip_grade": 0,
                "vip_etime": 0,
                "organism": [
                    
                ]
            }
        ]

        # 3. 战报日志 (对应 param1.log) - 暂时给空列表，不会报错
        battle_logs = []

        # 4. 点赞/关注数 (对应 param1.attention)
        attention_count = 88

        # ================= 组装发给客户端的最终 param1 =================
        panel_data = {
            "status": "success",
            "owner": owner_data,
            "opponent": opponents,
            "log": battle_logs,
            "attention": attention_count
        }
        
        return panel_data
    
    @staticmethod
    def set_organism(username, req_body):
        # 提取客户端发来的阵容数组
        org_list = []
        if isinstance(req_body, list) and len(req_body) > 0:
            if isinstance(req_body[0], list):
                org_list = req_body[0]
            else:
                org_list = req_body

        # 核心：将 [2, 1, 4, 3] 转换为字符串 "2,1,4,3" 并存入 SQLite 数据库！
        lineup_str = ",".join(map(str, org_list))
        update_arena_lineup(username, lineup_str)
        
        print(f"\n[斗技场] {username} 防守阵容已永久保存入库！阵容: {lineup_str}")
        return 999