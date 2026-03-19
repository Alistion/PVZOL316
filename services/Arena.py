# services/Arena.py
import json
from dal import get_arena_lineup, update_arena_lineup, get_all_users, get_user_organisms

class ArenaService:
    @staticmethod
    def _get_opponent_lineup_data(target_username):
        """
        精确匹配抓包的植物数据结构
        不再发送完整的植物属性，只发送斗技场特供的极简 6 属性
        """
        lineup_str = get_arena_lineup(target_username)
        if not lineup_str:
            return []
            
        orgs_db = get_user_organisms(target_username)
        orgs_dict = {}
        for org in orgs_db:
            try:
                data = json.loads(org['data'])
                data['id'] = org['id']
                orgs_dict[str(org['id'])] = data
            except:
                pass
                
        result = []
        for org_id in lineup_str.split(','):
            org_id_str = org_id.strip()
            if org_id_str and org_id_str in orgs_dict:
                raw_org = orgs_dict[org_id_str]
                
                # 【核心匹配】完全复原抓包里的 6 个极简字段和特殊数据类型
                # soul(Num), grade(Str), orid(Str), id(Str), fighting(Str), quality(Num)
                safe_org = {
                    "soul": int(raw_org.get("soul", 0)),
                    "grade": str(raw_org.get("grade", 100)),
                    "orid": str(raw_org.get("orderId", 176)),  # 官方叫 orid 而不是 orderId
                    "id": str(raw_org.get("id", 0)),
                    "fighting": str(raw_org.get("fighting", 99999)),
                    "quality": 18  # 官方用数字代替名字，18通常代表极品无极
                }
                result.append(safe_org)
        return result

    @staticmethod
    def get_arena_list(username):
        """获取斗技场对手列表面板数据 (消除断层，绝对连续排名版)"""
        
        from dal import get_arena_lineup, get_all_users
        
        # 1. 组装自己的防守植物 ID 数组
        lineup_str = get_arena_lineup(username)
        owner_organisms = []
        if lineup_str:
            for org_id in lineup_str.split(','):
                if org_id.strip():
                    owner_organisms.append(int(org_id.strip()))
        
        # 2. 获取全服所有玩家并进行“防断层”排序
        all_users = get_all_users()
        
        # 【核心修复】排序规则：
        # 如果已经打过斗技场有了 arena_rank，按 arena_rank 从小到大排；
        # 如果是新号 (arena_rank 没数据或者是 0)，放到最后面，按注册顺序(id)排。
        def sort_key(u):
            r = u.get('arena_rank') or 0
            if r > 0:
                return (0, r, u['id'])
            else:
                return (1, 0, u['id'])
                
        all_users.sort(key=sort_key)
        
        # 【核心修复】重新分配连续的、没有空隙的绝对排名 (1, 2, 3, 4...)
        my_rank = 9999
        for index, u in enumerate(all_users, start=1):
            u['_real_rank'] = index
            if u['username'] == username:
                my_rank = index

        owner_data = {
            "num": 5,        
            "rank": my_rank,
            "organisms": owner_organisms  
        }

        # 3. 组装对手列表
        opponents = []
        for u in all_users: # 这里的 all_users 已经是排序好的且赋好连续名次的了
            opp_username = u['username']
            if opp_username == username:
                continue 
                
            opp_rank = u['_real_rank']
            opp_uid = u['id'] + 100000
            opp_organisms = ArenaService._get_opponent_lineup_data(opp_username)
                        
            opponents.append({
                "face": u.get('avatar') or "/pvz/avatar/1.png",
                "vip_etime": "2000000000",   
                "organism": opp_organisms,
                "grade": str(u.get('level', 100)), 
                "nickname": opp_username,
                "vip_grade": "2",            
                "rank": opp_rank,            # <--- 绝对连续的排名！
                "userid": opp_uid            
            })
            
            # 只显示排名前 8 的对手
            if len(opponents) >= 8: 
                break

        # 4. 战报日志
        battle_logs = [
            {
                "a": "斗技场裁判",
                "b": username,
                "rank": str(my_rank),
                "b_info": "您当前的连续全服排名为",
                "a_info": "欢迎来到斗技场，"
            }
        ]

        panel_data = {
            "status": "success",
            "owner": owner_data,
            "opponent": opponents,
            "log": battle_logs,
            "attention": 0
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
        from dal import update_arena_lineup
        update_arena_lineup(username, lineup_str)
        
        print(f"\n[斗技场] {username} 防守阵容已永久保存入库！阵容: {lineup_str}")
        return {"status": "success"}