class DutyService:
    @staticmethod
    def get_all_duties(username):
        """
        获取玩家的任务列表 (主线、日常、支线、活跃)
        """
        # 【万能防弹模具】强制把所有变量变成 String，彻底杜绝 AS3 类型报错
        def make_task(t_id, title, dis, icon, state, cur_count, max_count, goto_id, r_money="", r_honor="", r_exp="", r_tools=None):
            if r_tools is None:
                r_tools = []
            
            # 格式化道具列表，强制 id 和 num 为字符串
            formatted_tools = [{"id": str(t["id"]), "num": str(t["num"])} for t in r_tools]

            return {
                "id": str(t_id),
                "title": str(title),
                "dis": str(dis),
                "icon": str(icon),
                "state": str(state),         # "0"未完成, "1"可领取
                "curCount": str(cur_count),  # 当前进度
                "maxCount": str(max_count),  # 最大进度
                "gotoId": str(goto_id),
                "reward": {
                    "money": str(r_money),   # 金币(没有就留空字符串"")
                    "honor": str(r_honor),   # 荣誉(没有就留空"")
                    "exp": str(r_exp),       # 经验(没有就留空"")
                    "tools": formatted_tools # 道具数组
                }
            }

        # 1. 组装主线任务 (mainTask)
        fake_main_tasks = [
            make_task(t_id=101055, title="玩家等级", dis="等级达到275级", icon=12, state=0, cur_count=0, max_count=1, goto_id=0, r_tools=[{"id": 103, "num": 550}]),
            make_task(t_id=109002, title="植物属性", dis="合成速度数值达到1e1", icon=6, state=0, cur_count=0, max_count=1, goto_id=0)
        ]

        # 2. 组装日常任务 (dailyTask)
        fake_daily_tasks = [
            make_task(t_id=301001, title="经验领取", dis="每日登陆领取全部经验值", icon=19, state=1, cur_count=1, max_count=1, goto_id=0, r_exp=5000)
        ]

        # 3. 组装支线任务 (sideTask)
        fake_side_tasks = [
            make_task(t_id=201009, title="金券消费", dis="累计使用2000金券", icon=19, state=0, cur_count=0, max_count=1, goto_id=0)
        ]

        # 4. 组装活跃任务 (activeTask)
        fake_active_tasks = []

        # 5. 拼装发给 Flash 的总字典
        return {
            "mainTask": fake_main_tasks,
            "dailyTask": fake_daily_tasks,
            "sideTask": fake_side_tasks,
            "activeTask": fake_active_tasks
        }