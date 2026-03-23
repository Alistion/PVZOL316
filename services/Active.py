# services/active.py
import time
import datetime
from dal import update_user_currencies, modify_tool_amount
from config import logger
class ActiveService:
    @staticmethod
    def get_sign_info(username):
        now = datetime.datetime.now()
        
        # 【核心修复模具】严格保证 type 在外面且为 String，num 和 id 在 data 里面且为 Number
        def make_reward(r_type, r_id, r_num):
            return {"type": str(r_type), "data": {"id": int(r_id), "num": int(r_num)}}
        
        # 1. 签到日历 signs
        signs_array = []
        for i in range(1, 32): 
            signs_array.append({
                "id": i,
                "count": -1,
                "state": 1 if i <= now.day else 0, # 1已签，0未签
                "rewards": [make_reward("2", 2, 50)] # 每天签到给50金券
            })
            
        # 2. 每日任务 missions (严格按照抓包全字符串)
        fake_missions = [
            {"id": "1", "dis": "今日消费50金券", "count": "0", "countmax": "1", "active": "20", "gotoId": "17"},
            {"id": "2", "dis": "参加1次斗技场", "count": "0", "countmax": "1", "active": "20", "gotoId": "8"},
            {"id": "3", "dis": "给世界树施肥1次", "count": "0", "countmax": "1", "active": "20", "gotoId": "6"},
            {"id": "4", "dis": "通关1次狩猎场", "count": "0", "countmax": "1", "active": "20", "gotoId": "15"},
            {"id": "5", "dis": "强化植物1次", "count": "0", "countmax": "1", "active": "20", "gotoId": "4"}
        ]
        
        # 3. 累计签到宝箱 signreward
        fake_signreward = [
            {"id": 1, "count": 5, "state": -1, "rewards": [make_reward("1", 2106, 100)]},
            {"id": 2, "count": 10, "state": -1, "rewards": [make_reward("1", 2106, 150)]},
            {"id": 3, "count": 15, "state": -1, "rewards": [make_reward("1", 2106, 200)]},
            {"id": 4, "count": 20, "state": -1, "rewards": [make_reward("1", 2107, 10)]},
            {"id": 5, "count": 25, "state": -1, "rewards": [make_reward("1", 2107, 20)]}
        ]
        
        # 4. 活跃度宝箱 activereward (完美复原抓包里的多个奖励物品组合！)
        fake_activereward = [
            {"id": 1, "count": 20, "state": -1, "rewards": [
                make_reward("1", 2106, 150)
            ]},
            {"id": 2, "count": 40, "state": -1, "rewards": [
                make_reward("1", 2106, 200),
                make_reward("1", 2107, 15)
            ]},
            {"id": 3, "count": 60, "state": -1, "rewards": [
                make_reward("1", 2106, 250),
                make_reward("1", 2107, 10),
                make_reward("1", 2108, 15)
            ]},
            {"id": 4, "count": 80, "state": -1, "rewards": [
                make_reward("1", 2107, 10),
                make_reward("1", 2108, 10),
                make_reward("1", 2109, 15),
                make_reward("1", 2121, 1)
            ]},
            {"id": 5, "count": 100, "state": -1, "rewards": [
                make_reward("1", 2107, 10),
                make_reward("1", 2108, 10),
                make_reward("1", 2109, 10),
                make_reward("1", 2121, 2)
            ]}
        ]
        
        # 5. 总字典
        panel_data = {
            "status": "success",
            "time": int(time.time()),
            "active": 0,             # Number
            "activemax": 100,        # Number
            "signcount": now.day - 1,# Number
            "signs": signs_array,
            "missions": fake_missions,
            "activereward": fake_activereward,
            "signreward": fake_signreward
        }
        
        return panel_data

    @staticmethod
    def process_sign_in(username):
        # 签到加钱逻辑
        
        update_user_currencies(username, money_delta=888)
        modify_tool_amount(username, tool_id=3008, amount_delta=1)
        return {"id": 1, "amount": 888}, {"id": 3008, "amount": 1}
    
    @staticmethod
    def get_banner(username, req_body):
        """
        处理获取活动 Banner 的请求 (api.banner.get)
        返回海报图片的 URL 和点击后跳转的网页 URL
        """
        logger.info(f"[活动系统] {username} 请求加载活动 Banner")
        
        # 你可以在这里配置你自己的图片路径和跳转链接
        # 图片路径最好是相对路径（放在你的资源目录下），或者是完整的外链 http://...
        return {
            "img": r"cache\pvz\events\1.png",  # 你的活动海报图片路径 (注意确保客户端能加载到这个文件)
            "url": "http://127.0.0.1:8080/activity/spin_win"        # 玩家点击参与活动后跳转的网页链接
        }
