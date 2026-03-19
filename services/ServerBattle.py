from dal import get_or_create_user,get_user_tools


class ServerBattleService:
    @staticmethod
    def get_qualifying_info(username):
        
        # 查玩家背包里，真实道具 850 的数量
        tools = get_user_tools(username)
        merit_item = next((t for t in tools if t['tool_id'] == 850), None)
        real_merit_amount = merit_item['amount'] if merit_item else 0
        
        fake_rewards = [{"amount": "10", "index": 1, "tool_id": "850"}]
        
        panel_data = {
            "reward": fake_rewards,
            "qualifyingEndTime": "2099-12-31 23:59:59",  
            "integral": 9999,                            
            "add_count": {"cost": 100, "n": 1},
            "remaining_challenges": 10,                  
            "nickname": username,                        
            "messages": [],                              
            "serverGroup": "1",                          
            "userGroup": "1",                            
            "meritorious": real_merit_amount   
        }
        return panel_data