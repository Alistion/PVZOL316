from dal import update_user_currencies, modify_tool_amount, add_organism, update_tree_height, clear_organisms, get_all_users, update_user_gm, reset_tree_gm
from config import logger



class GMService:
    @staticmethod
    def handle_post(form):
        action, username = form.get('action'), form.get('username')
        if not username: return
        
        if action == 'update_user':
            update_user_gm(username, form['money'], form['rmb_money'], form['level'])
        elif action == 'add_tool':
            modify_tool_amount(username, int(form['tool_id']), int(form['amount']))
        elif action == 'clear_orgs':
            clear_organisms(username)
        elif action == 'reset_tree':
            reset_tree_gm(username)
        elif action == 'add_plant':
            GMService._create_god_plant(username, form)

    @staticmethod
    def _create_god_plant(username, form):
        def get_big_int(field, default=0):
            try: return int(form.get(field, default))
            except: return default

        pid = get_big_int('pid', 771)
        hp = get_big_int('hp', 19139217953374379422862712240)
        attack = get_big_int('attack', 676478986767177892842475)
        miss = get_big_int('miss', 1024874993035086038953836)
        precision = get_big_int('precision', 2785645485227342847971847)
        new_miss = get_big_int('new_miss', 709102783312986521006659)
        new_precision = get_big_int('new_precision', 1085265587573216881070423)
        
        safe_org_data = {
            "orderId": pid, "grade": get_big_int('grade', 999), "quality_name": form.get('quality', '无极'),
            "im": get_big_int('im', 35), "ma": get_big_int('im', 35), "exp": 998000, "exp_max": 999000, "exp_min": 998000,
            "fighting": get_big_int('fighting', 216339651451215538145074615968), "hp": hp, "hp_max": hp, "attack": attack,
            "miss": miss, "precision": precision, "speed": get_big_int('speed', 107950559),
            "new_miss": new_miss, "new_precision": new_precision,
            "dq": 0, "gi": 0, "ss": 82836000, "ec": "", "pullulation": 40,
            "sh": hp, "sa": attack, "sm": miss, "spr": precision, "new_syn_precision": new_precision, "new_syn_miss": new_miss, 
            "tal_add": {"hp": 1682904810, "attack": 467473557, "speed": 201858, "miss": 373090536, "precision": 373090536},
            "soul_add": {"hp": 4417030804501728707741589372, "attack": 156110535407810282858753, "speed": 24911357, "miss": 236509613777327547366969, "precision": 642841265821694503294202},
            "sk": [{"id": 4098, "ba": 0, "oa": 0, "na": "狂战", "gr": 99}, {"id": 3698, "ba": 0, "oa": 0, "na": "狙击", "gr": 99}, {"id": 2498, "ba": 0, "oa": 0, "na": "穿刺", "gr": 99}, {"id": 6024, "ba": 0, "oa": 0, "na": "升魂", "gr": 25}], 
            "ssk": [{"id": 866, "name": "不朽之盾", "grade": 67, "type": 8}], 
            "tals": [{"id": f"talent_{i}", "level": 10} for i in range(1, 10)], "soul": get_big_int('soul', 10)
        }
        add_organism(username, pid, safe_org_data)
        logger.info(f"[GM] 给 {username} 创造了破界神宠 {pid}")