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
)

# ================= 价格内存缓存 =================
_TOOL_PRICE_CACHE = None


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
        modify_tool_amount(username, real_tool_id, buy_amount)
        logger.info(f"[商城] {username} 购买 {real_tool_id} x{buy_amount}")

        user_data = get_or_create_user(username)
        user_tools = get_user_tools(username)
        bought_amount = next(
            (t["amount"] for t in user_tools if t["tool_id"] == real_tool_id), 0
        )
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
        total_earn = 0

        if sell_type == 1:
            # ── 卖出道具 ──
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
            delete_organism_by_id(username, item_id)
            logger.info(
                f"[商城] {username} 出售植物(唯一ID:{item_id}) 获利:{total_earn}"
            )

        if total_earn > 0:
            update_user_currencies(username, money_delta=total_earn)

        return str(total_earn)
