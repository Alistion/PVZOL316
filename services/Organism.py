# services/Organism.py
import json
from dal.core import get_connection


class OrganismService:
    @staticmethod
    def get_evolution_cost(username, req_body):
        return 0 

    @staticmethod
    def execute_evolution(username, org_db_id, route_id):
        """执行进化：根据配方路线，变成真正的目标植物，并返回详细属性 XML"""
        
        # 进化路线映射表 (你后续可以扩充这个字典)
        route_to_target = {
            1597: 1705,  # 进化成 灭世星痕+10
            1598: 1706,  # 进化成 灭世星痕+11
            1599: 1707   # 进化成 灭世星痕+12
        }
        
        real_target_orid = route_to_target.get(route_id)
        
        if not real_target_orid:
            print(f"[合成屋报错] 找不到路线 {route_id} 对应的目标植物！")
            return '<?xml version="1.0" encoding="UTF-8"?><root><response><status>error</status></response></root>'

        with get_connection() as conn:
            # 1. 顺便获取一下玩家的金币和金券 
            user_row = conn.execute('SELECT money, rmb_money FROM users WHERE username = ?', (username,)).fetchone()
            
            # 获取金币和金券，如果没有查到给个默认值
            user_money = user_row['money'] if user_row else 99999999
            user_gold = user_row['rmb_money'] if user_row else 9999
            
            # 2. 获取植物数据
            org_row = conn.execute('SELECT data FROM user_organisms WHERE username = ? AND id = ?', (username, org_db_id)).fetchone()
            
            if org_row:
                org_data = json.loads(org_row['data'])
                
                # 3. 改变植物形态
                org_data['orderId'] = real_target_orid
                
                # 【可选】这里你可以写扣除金币的逻辑，比如 user_money -= 5250000，然后 UPDATE users 表
                
                # 保存植物
                conn.execute('UPDATE user_organisms SET data = ? WHERE username = ? AND id = ?', 
                             (json.dumps(org_data), username, org_db_id))
                conn.commit()
                
                # 4. 提取植物属性，准备发给 Flash (找不到的属性就给个夸张的默认值)
                picid = real_target_orid  # 进化后的新图片ID
                attack = org_data.get('attack', 999999)
                miss = org_data.get('miss', 100)
                precision = org_data.get('precision', 100)
                maxhp = org_data.get('hp_max', 9999999)
                pullulation = org_data.get('pullulation', 35) # 成长值
                quality = org_data.get('quality_name', '无极')
                
                print(f"[合成屋] {username} 成功将植物进化为 真正的新形态(orid:{real_target_orid})！")
                
                # 5. 拼装完美的、没有前导空格的 XML！
                xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
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
</root>"""
                # 使用 strip() 消除开头和结尾的任何多余空行/空格，确保 Flash 解析不报错
                return xml_response.strip()

        return '<?xml version="1.0" encoding="UTF-8"?><root><response><status>error</status></response></root>'
    
    @staticmethod
    def refresh_hp(username, req_body):
        """
        植物使用道具回血功能
        req_body: [操作类型(ORG_HP_x), 植物ID, 道具ID]
        """
        print(f"\n[植物回血] {username} 请求回血, 参数: {req_body}")
        
        if not req_body or len(req_body) < 2:
            return 0
            
        
        org_db_id = req_body[0]    # 植物的数据库 ID
        tool_id = req_body[1]      # 药水的道具 ID
        
        
        
        with get_connection() as conn:
            # 1. 扣除数据库里的药水 
            tool_row = conn.execute('SELECT amount FROM user_tools WHERE username = ? AND tool_id = ?', (username, tool_id)).fetchone()
            if not tool_row or tool_row['amount'] <= 0:
                print(f"[植物回血] 失败：道具 {tool_id} 数量不足！")
                return 0
                
            new_amount = tool_row['amount'] - 1
            if new_amount > 0:
                conn.execute('UPDATE user_tools SET amount = ? WHERE username = ? AND tool_id = ?', (new_amount, username, tool_id))
            else:
                conn.execute('DELETE FROM user_tools WHERE username = ? AND tool_id = ?', (username, tool_id))
                
            # 2. 给植物加满血！
            org_row = conn.execute('SELECT data FROM user_organisms WHERE username = ? AND id = ?', (username, org_db_id)).fetchone()
            if org_row:
                org_data = json.loads(org_row['data'])
                max_hp = org_data.get('hp_max', 999999) # 读取该植物的血量上限
                
                org_data['hp'] = max_hp  # 直接加满
                
                conn.execute('UPDATE user_organisms SET data = ? WHERE username = ? AND id = ?', (json.dumps(org_data), username, org_db_id))
                conn.commit()
                
                print(f"[植物回血] 成功！消耗药水 {tool_id}，植物 {org_db_id} 血量已回满({max_hp})！")
                
                # 3. 最关键的一步：直接返回数字，迎合 _loc7_.setHp(param2.toString())
                return max_hp
                
        return 0