from dal import modify_tool_amount,add_organism
import time
from config import logger


class OpenBoxService:
    @staticmethod
    def open_box(username, req_body):
        use_amount = 1
        tool_id = 3008
        try:
            if len(req_body) >= 3:
                tool_id, use_amount = int(req_body[1]), int(req_body[2])
        except: pass

        modify_tool_amount(username, tool_id, -use_amount)
        real_org_id = int(time.time() % 1000000)
        
        db_org_data = {
            "orderId": 1705, "attack": 1, "miss": 51034, "speed": 6663, 
            "hp": 9999999, "hp_max": 9999999, "grade": 200, "exp": 0, 
            "exp_max": 1000, "exp_min": 0, "im": 0, "precision": 40966, 
            "new_miss": 0, "new_precision": 0, "quality_name": "无极", 
            "dq": 0, "gi": 0, "ma": 0, "ss": 0, "ec": "", "sh": 0, "sa": 0, 
            "spr": 0, "sm": 0, "new_syn_precision": 0, "new_syn_miss": 0, 
            "fighting": 123269524, "pullulation": 40,
            "tal_add": {"hp": 999999, "attack": 99999, "speed": 2756, "miss": 41454, "precision": 37309},
            "soul_add": {"hp": 99999, "attack": 28048, "speed": 165, "miss": 2487, "precision": 22385},
            "tals": [{"id": f"talent_{i}", "level": 10} for i in range(1, 10)],
            "soul": 2
        }
        
        add_organism(username, db_org_data['orderId'], db_org_data)
        logger.info(f"[开箱] {username} 开启了神宠")
        
        amf_org_data = {"id": real_org_id, "orderId": db_org_data["orderId"], "hp_max": db_org_data["hp_max"], "exp_min": db_org_data["exp_min"], "precision": db_org_data["precision"], "hp": db_org_data["hp"], "fighting": db_org_data["fighting"], "speed": db_org_data["speed"], "new_miss": db_org_data["new_miss"], "miss": db_org_data["miss"], "exp_max": db_org_data["exp_max"], "quality_name": db_org_data["quality_name"], "new_precision": db_org_data["new_precision"], "attack": db_org_data["attack"], "grade": db_org_data["grade"], "pullulation": db_org_data["pullulation"], "exp": db_org_data["exp"]}
        
        return use_amount, amf_org_data