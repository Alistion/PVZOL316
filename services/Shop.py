# services/Shop.py
import json
import os
import xml.etree.ElementTree as ET

from config import logger
from dal import (
    delete_organism_by_id,
    get_or_create_user,
    get_user_tools,
    modify_tool_amount,
    update_user_currencies,
    add_organism,
    get_organism_by_id
)

# ================= 价格内存缓存 =================
_TOOL_PRICE_CACHE = None
_ORG_PRICE_CACHE = None

def _get_shop_items():
    try:
        with open("shop_config.json", "r", encoding="utf-8") as f:
            return json.load(f).get("items", [])
    except Exception as e:
        logger.error(f"读取商城配置失败: {e}")
        return []


def _format_shop_item(g):
    return {
        "id": str(g.get("id", "")),
        "p_id": str(g.get("p_id", "")),
        "type": str(g.get("type", "tool")),
        "price": str(g.get("price", "")),
        "num": str(g.get("num", "")),
        "exchange_tool_id": str(g.get("exchange_tool_id", "0")),
        "discount": str(g.get("discount", "0")),
    }


def _get_tool_sell_price(tool_id):
    global _TOOL_PRICE_CACHE
    if _TOOL_PRICE_CACHE is None:
        _TOOL_PRICE_CACHE = {}
        xml_path = os.path.join("cache", "pvz", "php_xml", "tool.xml")
        try:
            tree = ET.parse(xml_path)
            for item in tree.getroot().findall(".//item"):
                _TOOL_PRICE_CACHE[int(item.get("id", 0))] = int(
                    item.get("sell_price", 0)
                )
            logger.info(f"成功缓存 {len(_TOOL_PRICE_CACHE)} 个道具出售价格")
        except Exception as e:
            logger.error(f"读取 tool.xml 失败: {e}")
    return _TOOL_PRICE_CACHE.get(tool_id, 0)

def _get_org_sell_price(org_id):
    global _ORG_PRICE_CACHE
    if _ORG_PRICE_CACHE is None:
        _ORG_PRICE_CACHE = {}
        xml_path = os.path.join("cache", "pvz", "php_xml", "organism.xml")
        try:
            tree = ET.parse(xml_path)
            # 遍历 organism.xml 里的每一个植物 <item>
            for item in tree.getroot().findall(".//organisms/item"):
                o_id = int(item.get("id", 0))
                # 提取 xml 里配置的 sell_price 属性
                s_price = int(item.get("sell_price", 0))
                if o_id:
                    _ORG_PRICE_CACHE[o_id] = s_price
            logger.info(f"成功缓存 {len(_ORG_PRICE_CACHE)} 个植物出售价格")
        except Exception as e:
            logger.error(f"读取 organism.xml 失败: {e}")
    return _ORG_PRICE_CACHE.get(org_id, 0)


class ShopService:
    @staticmethod
    def get_shop_init():
        goods = [
            _format_shop_item(item)
            for item in _get_shop_items()
            if item.get("shop_type") == 3
        ]
        return {
            "type_all": {
                "exchange": 2,
                "game_coin": 1,
                "rmb": 3,
                "hot": 7,
                "vip": 6,
            },
            "money": 10,
            "time": 86400,
            "goods": goods,
        }

    @staticmethod
    def get_merchandises(shop_type):
        return [
            _format_shop_item(item)
            for item in _get_shop_items()
            if item.get("shop_type") == shop_type
        ]

    @staticmethod
    def buy_item(username, shop_item_id, buy_amount):
        item_config = next(
            (i for i in _get_shop_items() if i.get("id") == shop_item_id), None
        )
        if not item_config:
            return False

        real_tool_id = item_config["p_id"]
        total_cost = item_config["price"] * buy_amount
        shop_type = item_config.get("shop_type", 3)
        item_type = item_config.get("type", "tool")  # 获取商品类型（tool 或 organisms）
        exchange_id = 0

        # ── 扣款 ──
        if shop_type == 1:
            update_user_currencies(username, money_delta=-total_cost)
        elif shop_type in (3, 6, 7):
            update_user_currencies(username, rmb_delta=-total_cost)
        elif shop_type == 5:
            update_user_currencies(username, honor_delta=-total_cost)
        elif shop_type in (2, 4, 8):
            exchange_id = int(item_config.get("exchange_tool_id", 0))
            if exchange_id > 0:
                modify_tool_amount(username, exchange_id, -total_cost)
            else:
                logger.error(f"兑换失败：商品 {shop_item_id} 缺少 exchange_tool_id")
                return False

        # ── 发货 ──
        bought_amount = 0
        
        if item_type == "organisms":
            # 【如果是植物】：循环添加进 user_organisms 数据库表，并赋予 1 级基础属性
            for _ in range(buy_amount):
                base_org_data = {
                    "orderId": int(real_tool_id), "attack": 1000, "miss": 51034, "speed": 6663, 
                    "hp": 100, "hp_max": 100, "grade": 999, "exp": 0, 
                    "exp_max": 1000, "exp_min": 0, "im": 0, "precision": 40966, 
                    "new_miss": 0, "new_precision": 0, "quality_name": "劣质", 
                    "dq": 0, "gi": 0, "ma": 3, "ss": 0, "ec": "", "sh": 0, "sa": 0, 
                    "spr": 0, "sm": 0, "new_syn_precision": 0, "new_syn_miss": 0, 
                    "fighting": 1000, "pullulation": 40,
                    "tal_add": {"hp": 100, "attack": 100, "speed": 2756, "miss": 41454, "precision": 37309},
                    "soul_add": {"hp": 100, "attack": 100, "speed": 165, "miss": 2487, "precision": 22385},
                    "tals": [{"id": f"talent_{i}", "level": 0} for i in range(1, 10)],
                    "soul": 0
                }
                add_organism(username, int(real_tool_id), base_org_data)
                
            logger.info(f"[商城] {username} 购买植物 id:{real_tool_id} x{buy_amount}")
            bought_amount = buy_amount  # 植物是独立的，不计算叠加数量
            
        else:
            # 【如果是道具】：走老逻辑，叠加进 user_tools 数据库表
            modify_tool_amount(username, real_tool_id, buy_amount)
            logger.info(f"[商城] {username} 购买道具 {real_tool_id} x{buy_amount}")
            
            user_tools = get_user_tools(username)
            bought_amount = next(
                (t["amount"] for t in user_tools if t["tool_id"] == real_tool_id), 0
            )

        # ── 拼装返回数据 ──
        user_data = get_or_create_user(username)
        user_tools = get_user_tools(username)
        exchange_amount = (
            next((t["amount"] for t in user_tools if t["tool_id"] == exchange_id), 0)
            if exchange_id > 0
            else 0
        )

        return {
            "user": user_data,
            "bought_id": real_tool_id,
            "bought_amount": bought_amount,
            "exchange_id": exchange_id,
            "exchange_amount": exchange_amount,
        }

    @staticmethod
    def sell_item(username, sell_type, item_id, sell_amount):
        # 注意：文件顶部需要确保已经从 dal 导入了 get_organism_by_id
        # from dal import get_organism_by_id
        
        total_earn = 0

        if sell_type == 1:
            # ── 卖出道具 ──
            # 道具的 item_id 就是真实的道具 ID，可以直接查价格
            single_price = _get_tool_sell_price(item_id)
            total_earn = single_price * sell_amount
            modify_tool_amount(username, item_id, -sell_amount)
            logger.info(
                f"[商城] {username} 出售道具 {item_id} x{sell_amount} "
                f"(单价:{single_price}) 获利:{total_earn}"
            )

        elif sell_type == 2:
            # ── 卖出植物 ──
            # item_id 是 user_organisms 表的主键 id
            from dal import get_organism_by_id 
            org_data = get_organism_by_id(username, item_id)
            
            if org_data:
                real_plant_id = org_data.get("orderId", 0)
                plant_grade = org_data.get("grade", 1)
                
                # 【完美修复】：去 organism.xml 读取该植物的专属官方售价
                single_price = _get_org_sell_price(real_plant_id)
                
                single_price = single_price + (plant_grade - 1) * 20

                total_earn = single_price * sell_amount
                
                # 删掉植物
                delete_organism_by_id(username, item_id)
                logger.info(
                    f"[商城] {username} 出售植物(唯一ID:{item_id}, 真实ID:{real_plant_id}, 售价:{single_price}) 获利:{total_earn}"
                )

        if total_earn > 0:
            update_user_currencies(username, money_delta=total_earn)

        return str(total_earn)
