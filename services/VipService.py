class VipService:
    @staticmethod
    def get_vip_rewards(username):
        """
        获取 VIP 每日奖励与经验进度面板
        status: 1 可领取/已领取，-1 未达到条件不可领取
        """
        return {
            "reward": [
                {"min_exp": 0, "status": 1},
                {"min_exp": 2000, "status": 1},
                {"min_exp": 5000, "status": -1},
                {"min_exp": 10000, "status": -1}
            ],
            "vip_exp": 0,
            "user_day_max_exp": 400
        }