# services/shop.py
import os
import xml.etree.ElementTree as ET
from dal import update_user_currencies, modify_tool_amount, get_connection,get_or_create_user
from config import logger
import json
# ================= 价格内存缓存 =================
_TOOL_PRICE_CACHE = None

def get_shop_items():
    try:
        with open("shop_config.json", "r", encoding="utf-8") as f:
            # 【关键修改】原来是直接 return json.load(f)
            # 现在告诉它，只把 "items" 里面的数组取出来，"readme" 会被直接无视掉
            return json.load(f).get("items", [])
    except Exception as e:
        print(f"读取商城配置失败: {e}")
        return []

def get_tool_sell_price(tool_id):
    global _TOOL_PRICE_CACHE
    if _TOOL_PRICE_CACHE is None:
        _TOOL_PRICE_CACHE = {}
        xml_path = os.path.join('cache', 'pvz', 'php_xml', 'tool.xml')
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            for item in root.findall('.//item'):
                i_id = int(item.get('id', 0))
                price = int(item.get('sell_price', 0))
                _TOOL_PRICE_CACHE[i_id] = price
            logger.info(f"成功加载并缓存了 {len(_TOOL_PRICE_CACHE)} 个道具的出售价格！")
        except Exception as e:
            logger.error(f"读取 tool.xml 失败，请检查路径: {e}")
    return _TOOL_PRICE_CACHE.get(tool_id, 0)

class ShopService:
    @staticmethod
    def buy_item(username, shop_item_id, buy_amount):
        shop_items = get_shop_items()
        item_config = next((item for item in shop_items if item.get("id") == shop_item_id), None)
        if not item_config: return False
            
        real_tool_id = item_config["p_id"]
        total_cost = item_config["price"] * buy_amount
        shop_type = item_config.get("shop_type", 3)
        
        exchange_id = 0 # 记录可能消耗的实体道具（礼券/功勋）
        
        # --- 扣款逻辑 ---
        if shop_type == 1:
            update_user_currencies(username, money_delta=-total_cost)
        elif shop_type in [3, 6, 7]:
            update_user_currencies(username, rmb_delta=-total_cost)
        elif shop_type == 5:
            update_user_currencies(username, honor_delta=-total_cost) # 扣除荣誉
        elif shop_type in [2, 8]:  
            exchange_id = int(item_config.get("exchange_tool_id", 0))
            if exchange_id > 0:
                modify_tool_amount(username, exchange_id, -total_cost) # 扣实体道具
            else:
                return False
                
        # --- 发货逻辑 ---
        modify_tool_amount(username, real_tool_id, buy_amount)
        logger.info(f"[商城] {username} 购买 {real_tool_id} x{buy_amount}")
        
        # --- 组装对账清单 ---
        from dal import get_or_create_user, get_user_tools
        user_data = get_or_create_user(username)
        user_tools = get_user_tools(username)
        
        # 查出刚买到的物品最新数量
        bought_amount = next((t["amount"] for t in user_tools if t["tool_id"] == real_tool_id), 0)
        # 查出刚消耗掉的礼券/功勋牌的最新数量
        exchange_amount = next((t["amount"] for t in user_tools if t["tool_id"] == exchange_id), 0) if exchange_id > 0 else 0
        
        return {
            "user": user_data,
            "bought_id": real_tool_id,
            "bought_amount": bought_amount,
            "exchange_id": exchange_id,
            "exchange_amount": exchange_amount
        }

    @staticmethod
    def sell_item(username, sell_type, item_id, sell_amount):
        total_earn = 0
        
        if sell_type == 1:
            # ================= 卖出道具 =================
            # 精准读取 tool.xml 里的官方价格
            single_price = get_tool_sell_price(item_id)
            total_earn = single_price * sell_amount 
            
            # 扣除道具
            modify_tool_amount(username, item_id, -sell_amount)
            logger.info(f"[商城] {username} 出售道具ID: {item_id} x{sell_amount} (单价:{single_price}), 获利: {total_earn}")
            
        elif sell_type == 2:
            # ================= 卖出植物/生物 =================
            # 官方默认卖植物可能是 0 金币（根据你的抓包显示），这里我们先严格遵循抓包返回 0。
            # 如果你想让私服玩家卖植物能赚钱，可以把这里的 0 改成你想要的价格，比如 1000。
            total_earn = 0 
            
            # 重点：从数据库中删除这只被卖掉的植物！
            with get_connection() as conn:
                # 这里的 item_id 是这只植物在 user_organisms 表里的主键 id
                conn.execute('DELETE FROM user_organisms WHERE username = ? AND id = ?', (username, item_id))
                conn.commit()
                
            logger.info(f"[商城] {username} 出售了植物(唯一ID: {item_id}), 获利: {total_earn}")

        # 如果赚到钱了，就更新数据库余额
        if total_earn > 0:
            update_user_currencies(username, money_delta=total_earn)
            
        # 将算好的钱转换成 String 字符串返回，彻底消灭 NaN！
        return str(total_earn)