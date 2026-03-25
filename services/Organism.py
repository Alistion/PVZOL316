# services/Organism.py
import os
import xml.etree.ElementTree as ET

from config import logger
from dal import (
    consume_tool,
    get_tool_amount,
    get_or_create_user,
    get_organism_by_id,
    update_organism_data,
    update_user_currencies,
    get_organism_by_id,
    delete_organism_by_id
)


# ================= 技能数据内存缓存 =================
# 在这里手动配置：【技能书道具ID】 -> 【初次学习的技能ID】
_MANUAL_LEARN_MAP = {
    66: "2000",   # 假设 66 号道具（烈火书）用来学习 ID 为 2000 的技能（烈焰 lv1）
    63: "1898",   # 举例：63 号道具学习 2005 技能
    # 在这里继续添加你游戏里所有的技能书对应关系...
}

# ================= 2. 内存缓存库 =================
_SKILL_ID_MAP = None  # 建立以【技能 ID】为 Key 的索引

def _get_skill_by_tool(tool_id):
    """
    根据道具ID，先查手动映射表获取技能ID，再去缓存里获取完整的技能数据
    """
    global _SKILL_ID_MAP
    
    # 第一步：把所有技能按 ID 装进内存字典 (只执行一次)
    if _SKILL_ID_MAP is None:
        _SKILL_ID_MAP = {}
        from api_amf import _load_json_file
        skills_data = _load_json_file("skills.json") 
        
        iterable = skills_data if isinstance(skills_data, list) else skills_data.values()
        for skill in iterable:
            s_id = str(skill.get("id"))
            if s_id:
                _SKILL_ID_MAP[s_id] = skill
                
    # 第二步：根据玩家放进来的书 (tool_id)，去你的配置表里找对应的 技能ID
    target_skill_id = _MANUAL_LEARN_MAP.get(int(tool_id))
    
    # 如果这本“书”没在你的配置表里，说明它可能不是初学技能书
    if not target_skill_id:
        return None 
        
    # 第三步：拿着技能ID，去缓存里瞬间秒查完整的名字、描述、等级，并返回！
    return _SKILL_ID_MAP.get(str(target_skill_id))

# ================= 品质升级路线配置表 =================
# 格式: "当前品质": {"next": "下一阶品质", "tool_id": 需要消耗的品质书道具ID}

_QUALITY_UPGRADE_MAP = {
    "劣质": {"next": "普通", "tool_id": 16},
    "普通": {"next": "优秀", "tool_id": 16},  
    "优秀": {"next": "精良", "tool_id": 16},  
    "精良": {"next": "极品", "tool_id": 16},
    "极品": {"next": "史诗", "tool_id": 16},
    "史诗": {"next": "传说", "tool_id": 16},
    "传说": {"next": "神器", "tool_id": 16},
    "神器": {"next": "魔王", "tool_id": 16},
    "魔王": {"next": "战神", "tool_id": 16},
    "战神": {"next": "至尊", "tool_id": 16},
    "至尊": {"next": "魔神", "tool_id": 16},
    "魔神": {"next": "耀世", "tool_id": 834},
    "耀世": {"next": "不朽", "tool_id": 835},
    "不朽": {"next": "永恒", "tool_id": 836},
    "永恒": {"next": "太上", "tool_id": 1061},
    "太上": {"next": "混沌", "tool_id": 1063},
    "混沌": {"next": "无极", "tool_id": 1065},

    
}

# ── 进化路线映射表（启动时从 organism.xml 解析，全量缓存）────────────────────
# 结构：{ route_id (int): {"target": int, "money": int, "tools": [(tool_id, amount)]} }
_EVOLUTION_ROUTES: dict[int, dict] = {}


def _load_evolution_routes() -> dict[int, dict]:
    """
    解析 cache/pvz/php_xml/organism.xml，提取所有进化路线及其消耗。
    """
    routes: dict[int, dict] = {}
    xml_path = os.path.join("cache", "pvz", "php_xml", "organism.xml")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for org_item in root.findall(".//organisms/item"):
            for evo in org_item.findall("evolutions/item"):
                try:
                    route_id = int(evo.get("id", 0))
                    target_id = int(evo.get("target", 0))
                    money_cost = int(evo.get("money", 0))
                    
                    tools_cost = []
                    
                    # 1. 精准匹配你的 XML：读取 tool_id 属性
                    tool_id = evo.get("tool_id")
                    if tool_id:
                        t_id = int(tool_id)
                        # 如果标签里配了 tool_num 就按配的扣，没配就默认扣 1 个
                        t_amount = 1
                        tools_cost.append((t_id, t_amount))

                    if route_id and target_id:
                        routes[route_id] = {
                            "target": target_id,
                            "money": money_cost,
                            "tools": tools_cost
                        }
                except (ValueError, TypeError):
                    continue

        logger.info(f"[合成屋] 成功从 organism.xml 加载了 {len(routes)} 条进化路线及消耗配置")
    except FileNotFoundError:
        logger.error(f"[合成屋] 找不到 {xml_path}，进化功能将不可用")
    except ET.ParseError as e:
        logger.error(f"[合成屋] organism.xml 解析失败: {e}")

    return routes


# 模块加载时执行一次，之后直接查表，无需重复 IO
_EVOLUTION_ROUTES = _load_evolution_routes()


class OrganismService:
    @staticmethod
    def get_evolution_cost(username, req_body):
        return 0
    
    @classmethod
    def build_organism_amf_obj(cls, org_db_id, org_data):
        """
        统一封装植物的 AMF 返回结构
        将数据库中的 org_data 字典，转换为前端 Flash 严格要求的 String/Number 混合结构
        """
        if not org_data:
            return None
            
        return {
            "id": str(org_db_id),
            "orderId": str(org_data.get("orderId", 1)),
            "quality_name": org_data.get("quality_name", "普通"),
            "grade": str(org_data.get("grade", 1)),
            "exp": str(org_data.get("exp", 0)),
            "exp_max": str(org_data.get("exp_max", 1000)),
            "exp_min": str(org_data.get("exp_min", 0)),
            "hp": str(org_data.get("hp", 100)),
            "hp_max": str(org_data.get("hp_max", 100)),
            "attack": str(org_data.get("attack", 10)),
            "miss": str(org_data.get("miss", 10)),
            "new_miss": str(org_data.get("new_miss", org_data.get("miss", 10))),
            "precision": str(org_data.get("precision", 10)),
            "new_precision": str(org_data.get("new_precision", org_data.get("precision", 10))),
            "speed": str(org_data.get("speed", 10)),
            "fighting": str(org_data.get("fighting", 100)),
            "pullulation": str(org_data.get("pullulation", 10)),
            "soul": int(org_data.get("soul", 0)),  # 抓包中唯独 soul 是 Number
            
            "tal_add": org_data.get("tal_add", {"hp": "0", "attack": "0", "speed": "0", "miss": "0", "precision": "0"}),
            "soul_add": org_data.get("soul_add", {"hp": "0", "attack": "0", "speed": "0", "miss": "0", "precision": "0"}),
            "ssk": org_data.get("ssk", []),
            "skills": org_data.get("skills", []),
            
            "new_syn_precision": "0",
            "new_syn_miss": "0",
            "sa": "0", "sh": "0", "sm": "0", "ss": "0", "gi": "0", "spr": "0"
        }

    @staticmethod
    def execute_evolution(username, org_db_id, route_id):
        """
        执行进化：检查货币与道具是否充足，扣除消耗后变更植物 orderId 并保存。
        """
        _ERROR_XML = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<root><response><status>error</status></response></root>"
        )

        route_info = _EVOLUTION_ROUTES.get(route_id)
        if not route_info:
            logger.warning(
                f"[合成屋] 路线 {route_id} 在 organism.xml 中不存在，"
                f"共收录 {len(_EVOLUTION_ROUTES)} 条路线"
            )
            return _ERROR_XML

        real_target_orid = route_info["target"]
        money_cost = route_info["money"]
        tools_cost = route_info["tools"]

        # 1. 读取玩家货币
        user = get_or_create_user(username)
        user_money = user.get("money", 0)
        user_gold = user.get("rmb_money", 0)

        # 2. 校验金币
        if user_money < money_cost:
            logger.warning(f"[合成屋] 失败：{username} 金币不足，进化需 {money_cost}，当前 {user_money}")
            return _ERROR_XML

        # 3. 校验所需道具是否充足（前置遍历，避免扣了部分道具后发现下一种不够）
        for t_id, t_amount in tools_cost:
            if get_tool_amount(username, t_id) < t_amount:
                logger.warning(f"[合成屋] 失败：{username} 道具 {t_id} 数量不足，需 {t_amount}")
                return _ERROR_XML

        # 4. 校验植物数据
        org_data = get_organism_by_id(username, org_db_id)
        if org_data is None:
            logger.warning(f"[合成屋] 玩家 {username} 找不到植物 {org_db_id}")
            return _ERROR_XML

        # ==================== 执行扣除逻辑 ====================
        if money_cost > 0:
            update_user_currencies(username, money_delta=-money_cost)
            user_money -= money_cost  # 同步更新内存变量用于回写给Flash
            
        for t_id, t_amount in tools_cost:
            consume_tool(username, t_id, t_amount)
        # ====================================================

        # 变更形态并保存
        org_data["orderId"] = real_target_orid
        update_organism_data(username, org_db_id, org_data)

        logger.info(
            f"[合成屋] {username} 植物 {org_db_id} 成功进化为 orid:{real_target_orid}"
            f"（路线 {route_id}）。已扣除 {money_cost} 金币及道具: {tools_cost}"
        )

        # 提取属性，拼装返回给 Flash 的 XML
        picid = real_target_orid
        attack = org_data.get("attack", 999999)
        miss = org_data.get("miss", 100)
        precision = org_data.get("precision", 100)
        maxhp = org_data.get("hp_max", 9999999)
        pullulation = org_data.get("pullulation", 35)
        quality = org_data.get("quality_name", "无极")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <response><status>success</status></response>
    <org id="{org_db_id}">
        <picid>{picid}</picid>
        <attack>{attack}</attack>
        <miss>{miss}</miss>
        <new_miss>{miss}</new_miss>
        <new_precision>{precision}</new_precision>
        <maxhp>{maxhp}</maxhp>
        <pullulation>{pullulation}</pullulation>
        <precision>{precision}</precision>
        <quality>{quality}</quality>
    </org>
    <user rmb_money="{user_gold}" money="{user_money}" />
</root>""".strip()

    @staticmethod
    def refresh_hp(username, req_body):
        """
        植物使用道具回血。
        req_body: [植物数据库ID, 道具ID]
        """
        logger.info(f"[植物回血] {username} 请求回血, 参数: {req_body}")

        if not req_body or len(req_body) < 2:
            return 0

        org_db_id = req_body[0]
        tool_id = req_body[1]

        # 扣除药水（consume_tool 在数量不足时返回 False）
        if not consume_tool(username, tool_id):
            logger.warning(f"[植物回血] 失败：{username} 的道具 {tool_id} 数量不足！")
            return 0

        # 回满血
        org_data = get_organism_by_id(username, org_db_id)
        if org_data is None:
            logger.warning(f"[植物回血] 失败：找不到植物 {org_db_id}")
            return 0

        max_hp = org_data.get("hp_max", 999999)
        org_data["hp"] = max_hp
        update_organism_data(username, org_db_id, org_data)

        logger.info(
            f"[植物回血] 成功！消耗药水 {tool_id}，植物 {org_db_id} 血量回满({max_hp})"
        )
        return max_hp
    
    @staticmethod
    def quality_up(username, req_body):
        """
        处理植物品质提升请求
        req_body: [植物数据库ID]
        """
        if not req_body:
            return None

        org_db_id = int(req_body[0])
        org_data = get_organism_by_id(username, org_db_id)
        
        if not org_data:
            logger.warning(f"[植物系统] 品质升级失败：找不到植物 ID {org_db_id}")
            return None

        curr_quality = org_data.get("quality_name", "劣质")
        upgrade_info = _QUALITY_UPGRADE_MAP.get(curr_quality)

        if not upgrade_info:
            logger.warning(f"[植物系统] 品质升级失败：当前品质({curr_quality})已满级或未配置！")
            return None

        tool_id = upgrade_info["tool_id"]
        next_quality = upgrade_info["next"]

        # 1. 扣除对应的品质书
        
        if not consume_tool(username, tool_id, amount=1):
            logger.warning(f"[植物系统] 品质升级失败：道具 {tool_id} 数量不足！")
            return None

        # 2. 更新植物数据
        org_data["quality_name"] = next_quality
        
        # 象征性提升 20% 属性 (保持为整数)
        for attr in ["hp_max", "hp", "attack", "fighting", "precision", "miss", "speed"]:
            if attr in org_data:
                org_data[attr] = int(org_data[attr] * 1.2)
    
        # 3. 存回数据库
        update_organism_data(username, org_db_id, org_data)
        logger.info(f"[植物系统] {username} 的植物(ID:{org_db_id}) 品质升级成功: {curr_quality} -> {next_quality}")

        # 4. 【核心修复】：严格按照抓包的数据结构，拼装并返回一个完整的植物 Object
        # 抓包里大多数数字都是 String 类型，只有 soul 是 Number
        return OrganismService.build_organism_amf_obj(org_db_id, org_data)
    
    @staticmethod
    def quality12_up(username, req_body):
        """
        处理一键直升“魔神”的请求
        req_body: [植物数据库ID]
        """
        if not req_body:
            return None

        org_db_id = int(req_body[0])
        
        org_data = get_organism_by_id(username, org_db_id)
        
        if not org_data:
            logger.warning(f"[植物系统] 一键魔神失败：找不到植物 ID {org_db_id}")
            return None

        curr_quality = org_data.get("quality_name", "优秀")
        target_quality = "魔神"

        # 1. 定义品质阶梯，用于计算跨越了多少级
        quality_levels = [
            "优秀", "精良", "极品", "史诗", 
            "传说", "神器", "魔王", "战神", "至尊","魔神", "耀世"
        ]
        
        curr_idx = quality_levels.index(curr_quality) if curr_quality in quality_levels else 0
        target_idx = quality_levels.index(target_quality)
        
        # 如果当前品质已经是魔神或更高级(耀世)，则不允许使用
        if curr_idx >= target_idx:
            logger.warning(f"[植物系统] 一键魔神失败：当前品质({curr_quality})已达到或超过{target_quality}！")
            return None

        # 2. 扣除一键升魔神的专属道具
        # ⚠️ 这里你需要改成你游戏里真实的那本“一键魔神书”的道具 ID
        MAGIC_TOOL_ID = 1071  
        if not consume_tool(username, MAGIC_TOOL_ID, amount=1):
            logger.warning(f"[植物系统] 一键魔神失败：道具 {MAGIC_TOOL_ID} 数量不足！")
            return None

        # 3. 计算跨越阶数与属性补偿
        # 比如从优秀(2)升到魔神(11)，跨越了 9 阶，需要乘以 1.2 的 9 次方，保证属性不亏！
        tier_diff = target_idx - curr_idx
        multiplier = 1.2 ** tier_diff

        org_data["quality_name"] = target_quality
        for attr in ["hp_max", "hp", "attack", "fighting", "precision", "miss", "speed"]:
            if attr in org_data:
                org_data[attr] = int(org_data[attr] * multiplier)
    
        # 4. 存回数据库
        update_organism_data(username, org_db_id, org_data)
        logger.info(f"[植物系统] {username} 一键成神成功(ID:{org_db_id})! {curr_quality} -> {target_quality} (跨越{tier_diff}阶，属性x{multiplier:.2f})")

        # 5. 严格按照抓包的数据结构返回
        return OrganismService.build_organism_amf_obj(org_db_id, org_data)

    @staticmethod
    def synthesis(username, req_body):
        # 参数解析 [0, org1_id, org2_id, tool_id, toolsnum]
        args = req_body[0] if len(req_body) == 1 and isinstance(req_body[0], list) else req_body
        
        try:
            # 兼容性处理索引
            start_idx = 1 if args[0] == 0 else 0
            org1_id = int(args[start_idx])
            org2_id = int(args[start_idx + 1])
            tool_id = int(args[start_idx + 2])   # 合成书
            tool_num = int(args[start_idx + 3])  # 催化剂数量
        except: return None

        
        org1_data = get_organism_by_id(username, org1_id)
        org2_data = get_organism_by_id(username, org2_id)
        if not org1_data or not org2_data: return None

        # 1. 定义本次合成增加的数值 (全部初始化为 0)
        # 注意：源码里全是加法，所以后端只给“本次提升量”
        diff = {
            "hp": 0, "attack": 0, "speed": 0, 
            "precision": 0, "new_precision": 0,
            "miss": 0, "new_miss": 0
        }

        # 2. 根据合成书类型计算加成 
        # 催化剂(tool_num)越多，加成越高
        power = max(1, tool_num) * 10 

        if tool_id == 445: # HP合成
            diff["hp"] = power
        elif tool_id == 446: # 攻击合成
            diff["attack"] = power
        elif tool_id == 447: # 护甲合成
            diff["miss"] = power
        elif tool_id == 448: # 穿透合成
            diff["precision"] = power 
        elif tool_id == 449: # 速度合成
            diff["speed"] = power
        elif tool_id == 1093: # 闪避合成
            diff["new_miss"] = power 
        elif tool_id == 1094: # 命中合成
            diff["new_precision"] = power 
        

        # 3. 更新数据库里的植物数据
        org1_data["attack"] = int(org1_data.get("attack", 0)) + diff["attack"]
        org1_data["hp_max"] = int(org1_data.get("hp_max", 100)) + diff["hp"]
        org1_data["precision"] = int(org1_data.get("precision", 0)) + diff["precision"]
        org1_data["new_precision"] = int(org1_data.get("new_precision", 0)) + diff["new_precision"]
        org1_data["miss"] = int(org1_data.get("miss", 0)) + diff["miss"]
        org1_data["new_miss"] = int(org1_data.get("new_miss", 0)) + diff["new_miss"]
        org1_data["speed"] = int(org1_data.get("speed", 0)) + diff["speed"]

        # 计算总战力 
        new_fight = (int(org1_data["attack"]) * 2 + int(org1_data["hp_max"]) // 5)
        org1_data["fighting"] = new_fight

        # 4. 消耗材料和植物
        consume_tool(username, tool_id, 1) # 消耗1本书
        consume_tool(username, 450, tool_num) # 消耗催化剂数量

        delete_organism_by_id(username, org2_id)
        update_organism_data(username, org1_id, org1_data)

        # 5. 【按照源码要求返回】
        # _loc3_ 到 _loc9_ 全是 String(param2.xxx)
        # 只有 fight 是直接用的 param2.fight
        return {
            "hp": str(diff["hp"]),                # 本次加了多少血
            "attack": str(diff["attack"]),        # 本次加了多少攻
            "precision": str(diff["precision"]),  # 本次加了多少命中
            "new_precision": str(diff["new_precision"]),
            "miss": str(diff["miss"]),            # 本次加了多少闪避
            "new_miss": str(diff["new_miss"]),
            "speed": str(diff["speed"]),          # 本次加了多少速度
            "fight": str(new_fight)               # 总战力 (注意：只有它是传最终值)
        }
    
    @staticmethod
    def strengthen(username, req_body):
        """
        处理植物属性强化请求 (api.apiorganism.strengthen)
        """
        # 调试日志：确认前端传来的参数顺序
        logger.info(f"[强化系统] 收到 {username} 的强化请求，原始参数: {req_body}")
        
        # 处理可能的嵌套列表情况
        args = req_body[0] if len(req_body) == 1 and isinstance(req_body[0], list) else req_body
        
        try:
            # 根据 AS3 源码发包顺序: [action_type, org_id, tool_id]
            # action_type = int(args[0])
            org_db_id = int(args[0])
            tool_id = int(args[1])
        except Exception as e:
            logger.error(f"[强化系统] 参数解析失败: {e}")
            return None

        from dal import get_organism_by_id, update_organism_data, consume_tool
        
        org_data = get_organism_by_id(username, org_db_id)
        if not org_data:
            logger.warning(f"[强化系统] 找不到植物 ID: {org_db_id}")
            return None

        # 1. 扣除强化书 (每次消耗 1 本)
        if not consume_tool(username, tool_id, amount=1):
            logger.warning(f"[强化系统] 强化失败，道具 {tool_id} 数量不足！")
            return {"status": "error"}

        if tool_id == 450 : # 假设 action_type 5 是 LIFE
            add_val = 500
            org_data["hp_max"] = int(org_data.get("hp_max", 100)) + add_val
            org_data["hp"] = org_data["hp_max"] # 回满血
            logger.info(f"[强化系统] {username} 植物生命强化成功 +{add_val}")
            
        elif tool_id == 1014: # 攻击强化
            add_val = 12800000
            org_data["attack"] = int(org_data.get("attack", 10)) + add_val
            logger.info(f"[强化系统] {username} 植物攻击强化成功 +{add_val}")
            
        elif tool_id == 452: # 命中强化
            add_val = 30
            org_data["precision"] = int(org_data.get("precision", 10)) + add_val
            org_data["new_precision"] = int(org_data.get("new_precision", 10)) + add_val
            
        elif tool_id == 453: # 闪避强化
            add_val = 30
            org_data["miss"] = int(org_data.get("miss", 10)) + add_val
            org_data["new_miss"] = int(org_data.get("new_miss", 10)) + add_val
            
        elif tool_id == 454: # 速度强化
            add_val = 10
            org_data["speed"] = int(org_data.get("speed", 10)) + add_val
        else:
            # 兜底：如果没匹配上具体的书，默认加点攻击力防报错
            org_data["attack"] = int(org_data.get("attack", 10)) + 20

        # 重新计算战力
        new_fighting = (int(org_data.get("attack", 0)) * 2 + int(org_data.get("hp_max", 0)) // 5)
        org_data["fighting"] = new_fighting

        # 3. 保存到数据库
        update_organism_data(username, org_db_id, org_data)

        # 4. 【核心修复】：由于客户端调用了 readOrg(param2)，必须返回完整的植物 Object！
        return OrganismService.build_organism_amf_obj(org_db_id, org_data)
    
    @staticmethod
    def skill_learn(username, req_body):
        logger.info(f"[技能系统] 收到 {username} 的学习技能请求，原始参数: {req_body}")
        
        args = req_body[0] if len(req_body) == 1 and isinstance(req_body[0], list) else req_body
        
        try:
            if len(args) >= 3:
                action_type = int(args[0])
                org_db_id = int(args[1])
                tool_id = int(args[2])
            else:
                org_db_id = int(args[0])
                tool_id = int(args[1])
        except Exception as e:
            logger.error(f"[技能系统] 参数解析失败: {e}")
            return None

        org_data = get_organism_by_id(username, org_db_id)
        if not org_data:
            return None

        # 1. 自动去 JSON 里查这本技能书能学什么技能！
        skill_config = _get_skill_by_tool(tool_id)
        
        if not skill_config:
            logger.warning(f"[技能系统] 找不到道具 ID {tool_id} 对应的技能配置，请检查 skills.json！")
            return {"status": "error"}

        # 2. 扣除对应的技能书道具
        if not consume_tool(username, tool_id, amount=1):
            logger.warning(f"[技能系统] 学习失败，技能书 {tool_id} 数量不足！")
            return {"status": "error"}

        # 3. 将新技能加入植物的数据中
        if "skills" not in org_data or not isinstance(org_data["skills"], list):
            org_data["skills"] = []
            
        # ⚡ 核心：直接把 JSON 里的核心展示字段提取出来，塞给植物
        new_skill = {
            "id": str(skill_config.get("id", "")),
            "name": str(skill_config.get("name", "")),
            "grade": str(skill_config.get("grade", "1")),
            "group": str(skill_config.get("group", "")),
            "describe": str(skill_config.get("describe", ""))
        }
        
        # 同一类技能按 group 覆盖旧技能；没有同类技能时再新增
        skill_group = new_skill["group"]
        replaced = False
        for idx, old_skill in enumerate(org_data["skills"]):
            if str(old_skill.get("group", "")) == skill_group:
                org_data["skills"][idx] = new_skill
                replaced = True
                logger.info(
                    f"[技能系统] {username} 植物技能覆盖成功! "
                    f"[{skill_group}] {old_skill.get('name', '')} -> {new_skill['name']} lv{new_skill['grade']}"
                )
                break

        if not replaced:
            org_data["skills"].append(new_skill)
            logger.info(f"[技能系统] {username} 植物自动学习成功! 获得技能: {new_skill['name']} lv{new_skill['grade']}")

        # 4. 保存回数据库
        update_organism_data(username, org_db_id, org_data)

        # 5. 打包返回
        return OrganismService.build_organism_amf_obj(org_db_id, org_data)
    
    @staticmethod
    def skill_up(username, req_body):
        """
        处理植物技能升级请求 (api.apiorganism.skillUp)
        """
        logger.info(f"[技能系统] 收到 {username} 的技能升级请求，原始参数: {req_body}")
        
        args = req_body[0] if len(req_body) == 1 and isinstance(req_body[0], list) else req_body
        
        try:
            # 适配可能带有 ORG_UP (常量值) 的参数长度
            if len(args) >= 3:
                action_type = int(args[0])
                org_db_id = int(args[1])
                prev_skill_id = str(args[2])
            else:
                org_db_id = int(args[0])
                prev_skill_id = str(args[1])
        except Exception as e:
            logger.error(f"[技能系统] 参数解析失败: {e}")
            return None
    
        org_data = get_organism_by_id(username, org_db_id)
        if not org_data:
            return None

        # 1. 必须要用到我们之前在 _get_skill_by_tool 里建立的那个 _SKILL_ID_MAP
        global _SKILL_ID_MAP
        if not _SKILL_ID_MAP:
            # 防御性代码：万一服务器刚启动还没人学过技能，手动触发一次缓存加载
            from api_amf import _load_json_file
            _SKILL_ID_MAP = {}
            skills_data = _load_json_file("skills.json") 
            iterable = skills_data if isinstance(skills_data, list) else skills_data.values()
            for skill in iterable:
                s_id = str(skill.get("id"))
                if s_id:
                    _SKILL_ID_MAP[s_id] = skill

        # 2. 从缓存里找出当前的技能配置
        current_skill_config = _SKILL_ID_MAP.get(prev_skill_id)
        if not current_skill_config:
            logger.warning(f"[技能系统] 找不到当前技能 {prev_skill_id} 的配置！")
            return {"now_id": prev_skill_id, "prev_id": prev_skill_id} # 返回原样表示失败

        # 3. 提取升级所需的情报
        next_skill_id = str(current_skill_config.get("next_grade_id", ""))
        required_tool_id = int(current_skill_config.get("learn_tool", 0))

        # 4. 判断是否已经满级 (没有 next_grade_id 或者为 0)
        if not next_skill_id or next_skill_id == "0":
            logger.warning(f"[技能系统] 技能 {prev_skill_id} 已经满级，无法继续升级！")
            return {"now_id": prev_skill_id, "prev_id": prev_skill_id}

        # 5. 扣除升级必须的技能书/材料
        if required_tool_id > 0:
            if not consume_tool(username, required_tool_id, amount=1):
                logger.warning(f"[技能系统] 升级失败，缺少所需的材料书 ID: {required_tool_id}")
                return {"now_id": prev_skill_id, "prev_id": prev_skill_id}

        # 6. 获取下一级技能的完整配置，准备替换给植物
        next_skill_config = _SKILL_ID_MAP.get(next_skill_id)
        if not next_skill_config:
            logger.error(f"[技能系统] 找不到下一级技能 {next_skill_id} 的配置字典，请检查 skills.json！")
            return {"now_id": prev_skill_id, "prev_id": prev_skill_id}

        # 7. 更新数据库里该植物的 skills 列表
        if "skills" in org_data and isinstance(org_data["skills"], list):
            for idx, s in enumerate(org_data["skills"]):
                if str(s.get("id")) == prev_skill_id:
                    # 找到了老技能，把它原地替换成新一级的技能！
                    org_data["skills"][idx] = {
                        "id": next_skill_id,
                        "name": str(next_skill_config.get("name", "")),
                        "grade": str(next_skill_config.get("grade", "1")),
                        "group": str(next_skill_config.get("group", "")),
                        "describe": str(next_skill_config.get("describe", ""))
                    }
                    break

        # 8. 保存回数据库
        update_organism_data(username, org_db_id, org_data)
        logger.info(f"[技能系统] {username} 植物技能升级成功！ {prev_skill_id} -> {next_skill_id}")

        # 9. 【极简且特定的返回】：前端的回包逻辑只认 now_id 和 prev_id！
        return {
            "prev_id": prev_skill_id,
            "now_id": next_skill_id
        }
