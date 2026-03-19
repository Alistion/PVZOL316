# services/Organism.py
import os
import xml.etree.ElementTree as ET

from config import logger
from dal import (
    consume_tool,
    get_or_create_user,
    get_organism_by_id,
    update_organism_data,
)

# ── 进化路线映射表（启动时从 organism.xml 解析，全量缓存）────────────────────
# 结构：{ route_id (int): target_orid (int) }
_EVOLUTION_ROUTES: dict[int, int] = {}


def _load_evolution_routes() -> dict[int, int]:
    """
    解析 cache/pvz/php_xml/organism.xml，提取所有进化路线。

    XML 结构：
        <organisms>
          <item id="植物ID" ...>
            <evolutions>
              <item id="路线ID" target="目标植物ID" ... />
            </evolutions>
          </item>
        </organisms>

    返回 { 路线ID: 目标植物ID } 的字典。
    """
    routes: dict[int, int] = {}
    xml_path = os.path.join("cache", "pvz", "php_xml", "organism.xml")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for org_item in root.findall(".//organisms/item"):
            for evo in org_item.findall("evolutions/item"):
                try:
                    route_id = int(evo.get("id", 0))
                    target_id = int(evo.get("target", 0))
                    if route_id and target_id:
                        routes[route_id] = target_id
                except (ValueError, TypeError):
                    continue

        logger.info(f"[合成屋] 成功从 organism.xml 加载了 {len(routes)} 条进化路线")
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

    @staticmethod
    def execute_evolution(username, org_db_id, route_id):
        """
        执行进化：根据路线 ID 查表得到目标植物 orderId，
        更新数据库并返回给 Flash 的 XML 响应。
        """
        _ERROR_XML = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<root><response><status>error</status></response></root>"
        )

        real_target_orid = _EVOLUTION_ROUTES.get(route_id)
        if not real_target_orid:
            logger.warning(
                f"[合成屋] 路线 {route_id} 在 organism.xml 中不存在，"
                f"共收录 {len(_EVOLUTION_ROUTES)} 条路线"
            )
            return _ERROR_XML

        # 读取玩家货币（用于回写 XML）
        user = get_or_create_user(username)
        user_money = user.get("money", 0)
        user_gold = user.get("rmb_money", 0)

        # 读取植物数据
        org_data = get_organism_by_id(username, org_db_id)
        if org_data is None:
            logger.warning(f"[合成屋] 玩家 {username} 找不到植物 {org_db_id}")
            return _ERROR_XML

        # 变更形态并保存
        org_data["orderId"] = real_target_orid
        update_organism_data(username, org_db_id, org_data)

        logger.info(
            f"[合成屋] {username} 植物 {org_db_id} 成功进化为 orid:{real_target_orid}"
            f"（路线 {route_id}）"
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
