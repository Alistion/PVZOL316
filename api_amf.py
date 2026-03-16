# api_amf.py
import json
import time
from services import ShopService, ActiveService, OpenBoxService,ServerBattleService,DutyService,VipService

def get_shop_items():
    try:
        with open("shop_config.json", "r", encoding="utf-8") as f:
            # 【关键修改】原来是直接 return json.load(f)
            # 现在告诉它，只把 "items" 里面的数组取出来，"readme" 会被直接无视掉
            return json.load(f).get("items", [])
    except Exception as e:
        print(f"读取商城配置失败: {e}")
        return []
    
# 【新增】防转圈格式化模具：强制把所有数字转成 Flash 要求的 String
def format_shop_item(g):
    return {
        "id": str(g.get("id", "")),
        "p_id": str(g.get("p_id", "")),
        "type": str(g.get("type", "tool")),
        "price": str(g.get("price", "")),
        "num": str(g.get("num", "")),
        "exchange_tool_id": str(g.get("exchange_tool_id", "0")),
        "discount": str(g.get("discount", "0"))
    }

def route_amf_logic(api_name, req_body, current_user):
    # --- 活跃系统 ---
    if api_name == "api.active.getSignInfo":
        # 直接调用 services.py 里面刚写好的究极完美版字典并返回
        return ActiveService.get_sign_info(current_user)
        
    elif api_name == "api.active.sign":
        m_reward, t_reward = ActiveService.process_sign_in(current_user)
        return {"status": "success", "result": 1, "tools": [m_reward, t_reward]}
    
    # --- 商城系统 ---
    elif api_name == "api.shop.init":
        shop_items = get_shop_items()
        # 初始化大商城时，也要套用格式化模具！
        goods_array = [format_shop_item(item) for item in shop_items if item.get("shop_type") == 3]
        return {"type_all": {"exchange": 2, "game_coin": 1, "rmb": 3, "hot": 7, "vip": 6}, "money": 10, "time": 86400, "goods": goods_array}
    
    elif api_name == "api.shop.getMerchandises":
        shop_type = int(req_body[-1]) if req_body and len(req_body) > 0 else 3
        shop_items = get_shop_items()
        
        # 【致命修复】给功勋商店等其他商店套用字符串模具！
        goods_array = [format_shop_item(item) for item in shop_items if item.get("shop_type") == shop_type]
        
        # 老老实实返回一个纯数组，彻底告别转圈圈！
        return goods_array
    
    elif api_name == "api.shop.buy":
        buy_res = ShopService.buy_item(current_user, int(req_body[0]), int(req_body[1]))
        
        if buy_res:
            user_data = buy_res["user"]
            
            # 【完美复刻官方抓包】
            # Flash 需要一个 tool 对象，且 id 和 amount 必须是数字 (int)
            # 只有这步成功了，Flash 才会继续往下执行 UI 刷新的代码！
            return {
                "status": "success", 
                "money": user_data.get("money", 0),             # 兼容老商店的强同步
                "rmb_money": user_data.get("rmb_money", 0),
                "honor": user_data.get("honor", 0),
                "tool": {
                    "id": int(buy_res["bought_id"]),            # 必须转成 int (Number)
                    "amount": int(buy_res["bought_amount"])     # 必须转成 int (Number)
                }
            }
        return {"status": "error"}
        
    elif api_name == "api.shop.sell":
        if len(req_body) >= 3: 
            sell_type = int(req_body[0])     # 类型：1是道具，2是植物
            item_id = int(req_body[1])       # ID：道具ID 或 植物的唯一实例ID
            sell_amount = int(req_body[2])   # 数量
            
            # 让 Service 去处理扣除和加钱，并返回字符串格式的金额
            earned_money_str = ShopService.sell_item(current_user, sell_type, item_id, sell_amount)
            
            # 【终极修复】绝不能返回字典！Flash 要什么我们就给什么，直接返回字符串！
            return earned_money_str
            
        return "0"
    # --- 奖励系统 ---
    elif api_name in ["api.reward.openbox", "api.tool.useOf"]:
        use_amount, amf_org_data = OpenBoxService.open_box(current_user, req_body)
        return {"status": "success", "openAmount": use_amount, "prize_money": 8888, "prize_exp": 1000, "tools": [], "organisms": [amf_org_data]}
    # --- 跨服战系统 ---
    elif api_name == "api.serverbattle.qualifying":
        return ServerBattleService.get_qualifying_info(current_user)
    # --- 生物/植物系统 ---
    elif api_name == "api.apiorganism.getEvolutionOrgs":
        # 严格遵守抓包：没有可进化的植物时，官方直接返回 Null
        return None
    # --- 技能与其他 ---
    elif api_name == "api.apiskill.getAllSkills":
        try:
            with open("skills.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    elif api_name == "api.apiskill.getSpecSkillAll":
        try:
            with open("spec_skills.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    # --- 任务系统 ---
    elif api_name == "api.duty.getAll":
        return DutyService.get_all_duties(current_user)

    elif api_name == "api.duty.getDuty":
        # 【关键修复】客户端想弹窗，我们暂时返回 None 压制住它，防止它拿到 [] 后崩溃白屏
        return None
    # --- VIP 系统 ---
    elif api_name == "api.vip.rewards":
        return VipService.get_vip_rewards(current_user)
    
    elif api_name == "api.message.gets":
        return []
        
    return []