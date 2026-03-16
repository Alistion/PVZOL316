# api_amf.py
import json
import time
from services import ShopService, ActiveService, OpenBoxService, ServerBattleService, DutyService, VipService,StoneInstance,Instance


# 【新增】未实现接口的拦截预警器
def unimplemented_alert(api_name):
    # 1. 在控制台高亮提醒你
    # print(f"\n{'='*120}\n")
    print(f"-----------------------🚨 [开发提醒] 游戏请求了尚未实现的功能接口: {api_name}---------------------------")
    # print(f"{'='*120}\n")
    # 2. 返回标准的错误字典给 Flash，尝试弹窗并防止游戏白屏转圈
    return {"status": "error", "content": f"功能 [{api_name}] 后端暂未实现，请去 api_amf.py 补充代码！"}


def route_amf_logic(api_name, req_body, current_user):
    # ==========================================
    # ✅ 已经完美实现的系统接口
    # ==========================================
    
    # --- 活跃/签到系统 ---
    if api_name == "api.active.getSignInfo":
        return ActiveService.get_sign_info(current_user)
    elif api_name == "api.active.sign":
        m_reward, t_reward = ActiveService.process_sign_in(current_user)
        return {"status": "success", "result": 1, "tools": [m_reward, t_reward]}
    
    # --- 商城系统 ---
    elif api_name == "api.shop.init":
        return ShopService.get_shop_init()
    elif api_name == "api.shop.getMerchandises":
        shop_type = int(req_body[-1]) if req_body and len(req_body) > 0 else 3
        return ShopService.get_merchandises(shop_type)
    elif api_name == "api.shop.buy":
        buy_res = ShopService.buy_item(current_user, int(req_body[0]), int(req_body[1]))
        if buy_res:
            user_data = buy_res["user"]
            return {
                "status": "success", 
                "money": user_data.get("money", 0),
                "rmb_money": user_data.get("rmb_money", 0),
                "honor": user_data.get("honor", 0),
                "tool": { "id": int(buy_res["bought_id"]), "amount": int(buy_res["bought_amount"]) }
            }
        return {"status": "error"}
        
    elif api_name == "api.shop.sell":
        if len(req_body) >= 3: 
            return ShopService.sell_item(current_user, int(req_body[0]), int(req_body[1]), int(req_body[2]))
        return "0"
        
    # --- 奖励系统 (开宝箱) ---
    elif api_name in ["api.reward.openbox", "api.tool.useOf"]:
        use_amount, amf_org_data = OpenBoxService.open_box(current_user, req_body)
        return {"status": "success", "openAmount": use_amount, "prize_money": 8888, "prize_exp": 1000, "tools": [], "organisms": [amf_org_data]}
        
    # --- 跨服战系统 ---
    elif api_name == "api.serverbattle.qualifying":
        return ServerBattleService.get_qualifying_info(current_user)
        
    # --- 植物/技能系统 ---
    elif api_name == "api.apiorganism.getEvolutionOrgs": return None
    elif api_name == "api.apiskill.getAllSkills":
        try:
            with open("skills.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    elif api_name == "api.apiskill.getSpecSkillAll":
        try:
            with open("spec_skills.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return []
        
    # --- 任务与邮件系统 ---
    elif api_name == "api.duty.getAll": return DutyService.get_all_duties(current_user)
    elif api_name == "api.duty.getDuty": return None
    elif api_name == "api.vip.rewards": return VipService.get_vip_rewards(current_user)
    elif api_name == "api.message.gets": return []
    elif api_name == "api.active.getState": return 1

    # --- 宝石系统 ---
    elif api_name == "api.stone.getChapInfo":
        return StoneInstance.get_chap_info(current_user)
    elif api_name == "api.zombie.getInfo":
        return StoneInstance.get_zombie_info(current_user)
    
    # --- 副本系统 (InsideWorld / Fuben) ---
    elif api_name == "api.fuben.display":
        return Instance.InstanceService.display(current_user)

    # ==========================================
    # 🚧 尚未实现的功能占位符 (根据官方蓝图自动预警)
    # ==========================================

    # --- 1. 斗技场系统 (Arena) ---
    elif api_name in ["api.arena.awardWeek", "api.arena.getArenaList", "api.arena.getRankListOld", 
                      "api.arena.getAwardWeekInfo", "api.arena.getRankList", "api.arena.setOrganism", "api.arena.challenge"]:
        return unimplemented_alert(api_name)

    # --- 2. 花园系统 (Garden) ---
    elif api_name in ["api.garden.outAndStealAll", "api.garden.add", "api.garden.removeStateAll", 
                      "api.garden.organismReturnHome", "api.garden.challenge"]:
        return unimplemented_alert(api_name)

    # --- 3. 狩猎场/洞穴系统 (Hunting/Cave) ---
    elif api_name in ["api.cave.challenge", "api.cave.openCave", "api.cave.openGrid", "api.cave.useTimesands"]:
        return unimplemented_alert(api_name)

    # --- 4. 副本系统 (InsideWorld / Fuben) ---
    elif api_name in ["api.fuben.caveInfo", "api.fuben.openCave", "api.fuben.challenge",
                      "api.fuben.addChallengeCount", "api.fuben.addCaveChallengeCount", "api.fuben.top", 
                      "api.fuben.reward", "api.fuben.award"]:
        return unimplemented_alert(api_name)

    # --- 5. 植物强化与合成 (Organism / Tool) ---
    elif api_name in ["api.tool.synthesis", "api.apiorganism.refreshHp", "api.apiorganism.matureRecompute", 
                      "api.apiorganism.qualityUp", "api.apiorganism.quality12Up", "api.apiorganism.skillLearn", 
                      "api.apiorganism.skillUp", "api.apiorganism.activities", "api.apiorganism.getEvolutionCost",
                      "api.apiorganism.upgradeTalent", "api.apiorganism.restTalent", "api.apiorganism.strengthen",
                      "api.apiorganism.specSkillUp", "api.apiorganism.getAllExchangeInfo", "api.apiorganism.getOneExchangeInfo",
                      "api.apiorganism.exchangeOne", "api.apiorganism.exchangeAll"]:
        return unimplemented_alert(api_name)

    # --- 6. 领地系统 (Territory) ---
    elif api_name in ["api.territory.getTerritory", "api.territory.init", "api.territory.challenge", 
                      "api.territory.getMsg", "api.territory.recommen", "api.territory.quit", "api.territory.getAward"]:
        return unimplemented_alert(api_name)

    # --- 7. 跨服战系统 (Server Battle) ---
    elif api_name in ["api.serverbattle.knockoutReward", "api.serverbattle.knockoutAward", "api.serverbattle.getOpponent", 
                      "api.serverbattle.addChallengeCount", "api.serverbattle.challenge", "api.serverbattle.knockout", 
                      "api.serverbattle.fightLog", "api.serverbattle.getGroup", "api.serverbattle.guess", 
                      "api.serverbattle.ruleDescription", "api.serverbattle.signUp", "api.serverbattle.qualifyingReward", 
                      "api.serverbattle.qualifyingAward", "api.serverbattle.allGuess", "api.serverbattle.guessAward", 
                      "api.serverbattle.getIntegralTop", "api.serverbattle.guessTop", "api.serverbattle.message"]:
        return unimplemented_alert(api_name)

    # --- 8. 新手引导/活动/日常福利 (Guide / Active / Activity) ---
    elif api_name in ["api.apiactivity.info", "api.apiactivity.getActTool", "api.apiactivity.exchange", 
                      "api.guide.getGuideInfo", "api.guide.setCusReward", "api.guide.getCurAccSmall", 
                      "api.guide.setAccSmall", "api.guide.getCurAccBig", "api.guide.setAccBig", 
                      "api.guide.getsumtimeact", "api.guide.getsumtimereward", "api.guide.getDailyReward", 
                      "api.guide.getFirstReward", "api.guide.setFirstReward", "api.active.getCopyAllChapters", 
                      "api.active.getAllLevels", "api.active.challenge", "api.active.addCount", 
                      "api.active.getCopy", "api.banner.get", "api.gift.get"]:
        return unimplemented_alert(api_name)

    # --- 9. 摇钱树打僵尸 (Zombie) ---
    elif api_name in [ "api.zombie.beat", "api.zombie.addcount"]:
        return unimplemented_alert(api_name)

    # --- 10. 魔法石副本 (Stone) ---
    elif api_name in [ "api.stone.getCaveInfo", "api.stone.getRewardInfo", 
                      "api.stone.reward", "api.stone.getRankByCid", "api.stone.challenge", 
                      "api.stone.addCountByMoney", "api.stone.getCaveThrougInfo"]:
        return unimplemented_alert(api_name)

    # --- 11. 任务领取 (Duty) ---
    elif api_name in ["api.duty.getAward", "api.duty.acceptedDuty"]:
        return unimplemented_alert(api_name)

    # --- 12. VIP与抽奖 (VIP / Reward) ---
    elif api_name in ["api.vip.awards", "api.vip.startAuto", "api.vip.stopAuto", "api.vip.autoRewards", "api.reward.lottery"]:
        return unimplemented_alert(api_name)

    # --- 13. 商城其他功能 ---
    elif api_name in ["api.shop.reset", "api.shop.gemExchange"]:
        return unimplemented_alert(api_name)

    # --- 14. 账号锁定 (Apiuser) ---
    elif api_name == "api.apiuser.lock":
        return unimplemented_alert(api_name)

    # ==========================================
    # 💥 兜底拦截：连蓝图里都没写的隐藏 API
    # ==========================================
    else:
        print(f"\n[未知 API 警告] 抓到未记录的接口: {api_name}")
        return {"status": "error", "content": "未知的游戏接口！"}