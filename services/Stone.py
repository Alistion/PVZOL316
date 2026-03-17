# services/Stone.py
import time

class StoneInstance:
    @staticmethod
    def get_chap_info(username):
        """
        获取(宝石)副本的章节列表和挑战信息
        对应接口: api.stone.getChapInfo
        """
        # 官方数据里有 9 个大章，每个章节掉落不同的宝石
        stone_types = ["红宝石", "蓝宝石", "烟晶石", "=白宝石", "绿宝石", "日光石", "黑曜石", "紫晶石", "天河石"]
        
        chap_info_array = []
        
        # 动态生成 9 个章节的数据
        for i in range(1, 10):
            stone_name = stone_types[i-1]
            chap_info_array.append({
                "star": 153,              # 当前获得星星 (Number)
                "total_star": 216,        # 总星星数 (Number)
                "name": f"副本{i}-3",       # 章节名称 (String)
                "desc": f"副本{i}-3",       # 章节描述 (String)
                "stone": [                # 掉落预览 (Array of String)
                    f"2级{stone_name}", 
                    f"3级{stone_name}", 
                    "4级宝石箱"
                ]
            })
        
        # 组装外层的面板数据
        panel_data = {
            "chap_info": chap_info_array,
            "next_time": 999999,          # 倒计时 (Number)
            "buy_max_count": 999999,      # 最大可购买次数 (Number)
            "cha_count": 1951             # 剩余挑战次数 (Number)
        }
        
        return panel_data
    
    @staticmethod
    def get_zombie_info(username):
        """
        获取矿坑夺宝的初始化面板数据
        对应接口: api.zombie.getInfo
        """
        panel_data = {
            "helper": 3,
            "level": 1,
            "rate": 999,
            "can_buy_count": 999,
            "probability": 999,
            "count": 10,
            "max_multiple": 8,
            "zombies": [
                {
                    "dt": 1,
                    "bs": 1,
                    "rd": [
                        [[1002, 0]],  
                        [[1002, 0]]
                    ],
                    "na": "",
                    "pt": 9,
                    "hm": 666,        # 僵尸总血量
                    "hp": 666,        # 僵尸当前血量
                    "pi": 1,
                    "id": 1
                }
            ],
            "level_reward": [
                {"amount": 0, "id": 1002},
                {"amount": 0, "id": 1002}
            ]
        }
        return panel_data