# services/Reward.py

class RewardService:
    @staticmethod
    def get_lottery_prize(username, req_body):
        """
        处理登录/离线/活动抽奖奖励
        返回的格式必须严格匹配 GetPrizes_rpc.getAllAwards
        """
        print(f"\n[奖励系统] {username} 触发了领奖接口，发来的参数/Key: {req_body}")
        
        # 假设我们要送给玩家 10 个高级进化材料(ID: 859) 和 5 瓶大血药(ID: 14)
        # 这里你可以后续加上真实的数据库写入逻辑：给 user_tools 表增加这些道具
        
        # 严格按照 AS3 源码构造发奖字典：
        response_data = {
            "tools": [
                {
                    "id": 859,     # 道具图鉴ID
                    "amount": 10   # 赠送数量
                },
                {
                    "id": 14,      # 药水道具ID
                    "amount": 5    # 赠送数量
                }
            ],
            # 如果不想送植物，可以给个空数组，防止 getOrganisms 报错
            "organisms": [] 
        }
        
        print(f"[奖励系统] 成功发放奖励！下发数据: {response_data}")
        return response_data