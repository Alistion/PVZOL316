# api_amf.py
import json

from services import (
    ActiveService,
    ArenaService,
    DutyService,
    InstanceService,
    OpenBoxService,
    OrganismService,
    RewardService,
    ServerBattleService,
    ShopService,
    StoneInstance,
    VipService,
)

# ── 工具函数 ──────────────────────────────────────────────────────────────────


def _load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ── 需要多步骤组装的接口，抽成独立函数保持分发表整洁 ─────────────────────────


def _do_sign(user, _body):
    m_reward, t_reward = ActiveService.process_sign_in(user)
    return {"status": "success", "result": 1, "tools": [m_reward, t_reward]}


def _do_buy(user, body):
    buy_res = ShopService.buy_item(user, int(body[0]), int(body[1]))
    if not buy_res:
        return {"status": "error"}
    ud = buy_res["user"]
    return {
        "status": "success",
        "money": ud.get("money", 0),
        "rmb_money": ud.get("rmb_money", 0),
        "honor": ud.get("honor", 0),
        "tool": {
            "id": int(buy_res["bought_id"]),
            "amount": int(buy_res["bought_amount"]),
        },
    }


def _do_sell(user, body):
    if len(body) >= 3:
        return ShopService.sell_item(user, int(body[0]), int(body[1]), int(body[2]))
    return "0"


def _do_merchandises(user, body):
    shop_type = int(body[-1]) if body else 3
    return ShopService.get_merchandises(shop_type)


def _do_openbox(user, body):
    use_amount, amf_org_data = OpenBoxService.open_box(user, body)
    return {
        "status": "success",
        "openAmount": use_amount,
        "prize_money": 8888,
        "prize_exp": 1000,
        "tools": [],
        "organisms": [amf_org_data],
    }


# ── 已实现接口的分发表 ────────────────────────────────────────────────────────
#
# 格式：  "api.名称": handler(current_user, req_body) -> Any
#
# 规则：
#   - 逻辑简单（一行能写完）→ 直接用 lambda
#   - 逻辑复杂（多步骤）     → 单独定义函数，此处只填函数名
#
_AMF_ROUTES: dict = {
    # ── 活跃 / 签到 ──────────────────────────────────────────────────────────
    "api.active.getSignInfo": lambda u, b: ActiveService.get_sign_info(u),
    "api.active.sign": _do_sign,
    "api.active.getState": lambda u, b: 1,
    # ── 商城 ──────────────────────────────────────────────────────────────────
    "api.shop.init": lambda u, b: ShopService.get_shop_init(),
    "api.shop.getMerchandises": _do_merchandises,
    "api.shop.buy": _do_buy,
    "api.shop.sell": _do_sell,
    # ── 奖励 / 开宝箱 ─────────────────────────────────────────────────────────
    "api.reward.openbox": _do_openbox,
    "api.tool.useOf": _do_openbox,
    "api.reward.lottery": lambda u, b: RewardService.get_lottery_prize(u, b),
    # ── 跨服战 ────────────────────────────────────────────────────────────────
    "api.serverbattle.qualifying": lambda u, b: ServerBattleService.get_qualifying_info(
        u
    ),
    # ── 植物 / 技能 ───────────────────────────────────────────────────────────
    "api.apiorganism.getEvolutionCost": lambda u, b: OrganismService.get_evolution_cost(
        u, b
    ),
    "api.apiorganism.refreshHp": lambda u, b: OrganismService.refresh_hp(u, b),
    "api.apiorganism.getEvolutionOrgs": lambda u, b: None,
    "api.apiskill.getAllSkills": lambda u, b: _load_json_file("skills.json"),
    "api.apiskill.getSpecSkillAll": lambda u, b: _load_json_file("spec_skills.json"),
    # ── 任务 / 邮件 ───────────────────────────────────────────────────────────
    "api.duty.getAll": lambda u, b: DutyService.get_all_duties(u),
    "api.duty.getDuty": lambda u, b: None,
    "api.message.gets": lambda u, b: [],
    # ── VIP ───────────────────────────────────────────────────────────────────
    "api.vip.rewards": lambda u, b: VipService.get_vip_rewards(u),
    # ── 宝石副本 ──────────────────────────────────────────────────────────────
    "api.stone.getChapInfo": lambda u, b: StoneInstance.get_chap_info(u),
    "api.zombie.getInfo": lambda u, b: StoneInstance.get_zombie_info(u),
    # ── 副本 (InsideWorld / Fuben) ────────────────────────────────────────────
    "api.fuben.display": lambda u, b: InstanceService.display(u),
    # ── 斗技场 ────────────────────────────────────────────────────────────────
    "api.arena.getArenaList": lambda u, b: ArenaService.get_arena_list(u),
    "api.arena.setOrganism": lambda u, b: ArenaService.set_organism(u, b),
}


# ── 已知但尚未实现的接口（仅做预警，不让游戏白屏转圈）────────────────────────

_UNIMPLEMENTED: set = {
    # 斗技场
    "api.arena.awardWeek",
    "api.arena.getRankListOld",
    "api.arena.getAwardWeekInfo",
    "api.arena.getRankList",
    "api.arena.challenge",
    # 花园
    "api.garden.outAndStealAll",
    "api.garden.add",
    "api.garden.removeStateAll",
    "api.garden.organismReturnHome",
    "api.garden.challenge",
    # 狩猎场 / 洞穴
    "api.cave.challenge",
    "api.cave.openCave",
    "api.cave.openGrid",
    "api.cave.useTimesands",
    # 副本进阶
    "api.fuben.caveInfo",
    "api.fuben.openCave",
    "api.fuben.challenge",
    "api.fuben.addChallengeCount",
    "api.fuben.addCaveChallengeCount",
    "api.fuben.top",
    "api.fuben.reward",
    "api.fuben.award",
    # 植物强化 / 合成
    "api.tool.synthesis",
    "api.apiorganism.matureRecompute",
    "api.apiorganism.qualityUp",
    "api.apiorganism.quality12Up",
    "api.apiorganism.skillLearn",
    "api.apiorganism.skillUp",
    "api.apiorganism.activities",
    "api.apiorganism.upgradeTalent",
    "api.apiorganism.restTalent",
    "api.apiorganism.strengthen",
    "api.apiorganism.specSkillUp",
    "api.apiorganism.getAllExchangeInfo",
    "api.apiorganism.getOneExchangeInfo",
    "api.apiorganism.exchangeOne",
    "api.apiorganism.exchangeAll",
    # 领地
    "api.territory.getTerritory",
    "api.territory.init",
    "api.territory.challenge",
    "api.territory.getMsg",
    "api.territory.recommen",
    "api.territory.quit",
    "api.territory.getAward",
    # 跨服战进阶
    "api.serverbattle.knockoutReward",
    "api.serverbattle.knockoutAward",
    "api.serverbattle.getOpponent",
    "api.serverbattle.addChallengeCount",
    "api.serverbattle.challenge",
    "api.serverbattle.knockout",
    "api.serverbattle.fightLog",
    "api.serverbattle.getGroup",
    "api.serverbattle.guess",
    "api.serverbattle.ruleDescription",
    "api.serverbattle.signUp",
    "api.serverbattle.qualifyingReward",
    "api.serverbattle.qualifyingAward",
    "api.serverbattle.allGuess",
    "api.serverbattle.guessAward",
    "api.serverbattle.getIntegralTop",
    "api.serverbattle.guessTop",
    "api.serverbattle.message",
    # 新手引导 / 活动 / 日常福利
    "api.apiactivity.info",
    "api.apiactivity.getActTool",
    "api.apiactivity.exchange",
    "api.guide.getGuideInfo",
    "api.guide.setCusReward",
    "api.guide.getCurAccSmall",
    "api.guide.setAccSmall",
    "api.guide.getCurAccBig",
    "api.guide.setAccBig",
    "api.guide.getsumtimeact",
    "api.guide.getsumtimereward",
    "api.guide.getDailyReward",
    "api.guide.getFirstReward",
    "api.guide.setFirstReward",
    "api.active.getCopyAllChapters",
    "api.active.getAllLevels",
    "api.active.challenge",
    "api.active.addCount",
    "api.active.getCopy",
    "api.banner.get",
    "api.gift.get",
    # 摇钱树打僵尸
    "api.zombie.beat",
    "api.zombie.addcount",
    # 魔法石副本进阶
    "api.stone.getCaveInfo",
    "api.stone.getRewardInfo",
    "api.stone.reward",
    "api.stone.getRankByCid",
    "api.stone.challenge",
    "api.stone.addCountByMoney",
    "api.stone.getCaveThrougInfo",
    # 任务领取
    "api.duty.getAward",
    "api.duty.acceptedDuty",
    # VIP / 抽奖进阶
    "api.vip.awards",
    "api.vip.startAuto",
    "api.vip.stopAuto",
    "api.vip.autoRewards",
    # 商城其他
    "api.shop.reset",
    "api.shop.gemExchange",
    # 账号锁定
    "api.apiuser.lock",
}


# ── 核心分发函数（对外暴露的唯一入口）───────────────────────────────────────


def route_amf_logic(api_name: str, req_body, current_user: str):
    # 1. 查已实现表
    handler = _AMF_ROUTES.get(api_name)
    if handler is not None:
        return handler(current_user, req_body)

    # 2. 查已知但未实现表 → 友好预警，避免游戏白屏
    if api_name in _UNIMPLEMENTED:
        print(f"🚨 [开发提醒] 尚未实现的接口: {api_name}")
        return {
            "status": "error",
            "content": f"功能 [{api_name}] 后端暂未实现，请在 api_amf.py 补充！",
        }

    # 3. 完全未知的接口 → 报警
    print(f"[未知 API] 抓到未记录的接口: {api_name}")
    return {"status": "error", "content": "未知的游戏接口！"}
