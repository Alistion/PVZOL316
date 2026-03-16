# api_xml.py
import json
from dal import get_or_create_user, get_user_tools, get_user_organisms
from services import TreeService

def build_user_xml(username):
    user = get_or_create_user(username)
    
    def safe_num(val, default=0):
        try:
            if val is None or val == "": return default
            return min(int(float(val)), 2100000000)
        except:
            return default

    # 经过安检门过滤数据
    money = safe_num(user.get('money'), 0)
    rmb = safe_num(user.get('rmb_money'), 0)
    level = safe_num(user.get('level'), 100)
    t_height = safe_num(user.get('tree_height'), 0)
    honor_val = safe_num(user.get('honor'), 0) 
    
    # # 【新增】获取真实的功勋值
    # merit_val = safe_num(user.get('merit'), 0)

    # 【关键修复】在 <user> 标签的末尾，加上 merit="{merit_val}" meritorious="{merit_val}"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <response><status>success</status></response>
        <user id="{user['id']}" name="{user['username']}" charm="999" money="{money}" date_award="1" reward_daily="1" has_reward_cus="1" has_reward_once="1" has_reward_sum="1" has_reward_first="1" state="" rmb_money="{rmb}" open_cave_grid="16" wins="999" is_new="0" login_reward="1" invite_amount="0" use_invite_num="0" max_use_invite_num="10" lottery_key="99" banner_num="0" banner_url="/pvz/events/" hasActivitys="1" face_url="" face="1" vip_grade="10" vip_etime="1893427200" vip_restore_hp="1" is_auto="0" serverbattle_status="3" IsNewTaskSystem="1" registrationReward="0" stone_cha_count="0" vip_exp="99999" >
            <arena_rank_date old_start="2026-01-01" old_end="2026-12-31" />
            <tree height="{t_height}" today="1" today_max="1000" />
            <grade id="{level}" exp="99999" exp_min="0" exp_max="100000" today_exp="0" today_exp_max="1000" />
            <garden amount="10" organism_amount="10" garden_organism_amount="10" />
            <cave amount="0" max_amount="2250" open_grid_grade="10" open_grid_money="1000" />
            <territory honor="{honor_val}" amount="5" max_amount="10" />
            <fuben fuben_lcc="5" />
            <copy_active state="1" />
            <copy_zombie state="0" />
            <friends amount="0" page_count="1" current="1" page_size="10" />
        </user>
    </root>"""

def build_warehouse_xml(username):
    tools = get_user_tools(username)
    orgs = get_user_organisms(username)
    hidden_tool_ids = {2}
    tools_xml = "".join([f'<item id="{t["tool_id"]}" amount="{t["amount"]}" />' for t in tools if t["amount"] > 0 and t["tool_id"] not in hidden_tool_ids])
    orgs_xml = ""
    for o in orgs:
        try:
            d = json.loads(o["data"])
            ta, sa = d.get("tal_add", {}), d.get("soul_add", {})
            sk_xml = "".join([f'<item id="{s["id"]}" ba="{s.get("ba",0)}" oa="{s.get("oa",0)}" na="{s["na"]}" gr="{s["gr"]}" />' for s in d.get("sk", [])])
            ssk_xml = "".join([f'<item id="{s["id"]}" name="{s["name"]}" grade="{s["grade"]}" type="{s["type"]}" />' for s in d.get("ssk", [])])
            tals_xml = "".join([f'<tal id="{t["id"]}" level="{t["level"]}" />' for t in d.get("tals", [])])

            orgs_xml += f'''
            <item id="{o["id"]}" pid="{d.get("orderId", 176)}" at="{d.get("attack", 999999)}" mi="{d.get("miss", 100)}" sp="{d.get("speed", 100)}" hp="{d.get("hp", 999999)}" hm="{d.get("hp_max", 999999)}" gr="{d.get("grade", 100)}" ex="{d.get("exp", 0)}" ema="{d.get("exp_max", 1000)}" emi="{d.get("exp_min", 0)}" im="{d.get("im", 0)}" pr="{d.get("precision", 100)}" new_miss="{d.get("new_miss", 0)}" new_precision="{d.get("new_precision", 0)}" qu="{d.get("quality_name", "无极")}" dq="{d.get("dq", 0)}" gi="{d.get("gi", 0)}" ma="{d.get("ma", 0)}" ss="{d.get("ss", 0)}" ec="" sh="{d.get("sh", 0)}" sa="{d.get("sa", 0)}" spr="{d.get("spr", 0)}" sm="{d.get("sm", 0)}" new_syn_precision="{d.get("new_syn_precision", 0)}" new_syn_miss="{d.get("new_syn_miss", 0)}" fight="{d.get("fighting", 123269524)}">
                <tal_add hp="{ta.get("hp", 0)}" attack="{ta.get("attack", 0)}" speed="{ta.get("speed", 0)}" miss="{ta.get("miss", 0)}" precision="{ta.get("precision", 0)}" />
                <soul_add hp="{sa.get("hp", 0)}" attack="{sa.get("attack", 0)}" speed="{sa.get("speed", 0)}" miss="{sa.get("miss", 0)}" precision="{sa.get("precision", 0)}" />
                <sk>{sk_xml}</sk><ssk>{ssk_xml}</ssk><tals>{tals_xml}</tals><soul>{d.get("soul", 2)}</soul>
            </item>'''
        except Exception: pass

    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <response><status>success</status></response>
        <warehouse tool_grid_amount="200" organism_grid_amount="200">
            <open_info><organism grade="10" money="1000" /><tool grade="10" money="1000" /></open_info>
            <tools>{tools_xml}</tools>
            <organisms>{orgs_xml}<organisms_arena ids="" /><organisms_territory ids="-1,-1,-1,-1,-1" /><organisms_serverbattle ids="" /></organisms>
        </warehouse>
    </root>"""

def handle_tree_fertilize(current_user):
    new_height = TreeService.fertilize(current_user)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <data>
        <response><status>success</status></response>
        <tree height="{new_height}" times="9999" message="世界之树长高了！获得了丰厚奖励！" />
        <awards><tools><item id="1" amount="8888" /><item id="3008" amount="10" /></tools></awards>
    </data>"""