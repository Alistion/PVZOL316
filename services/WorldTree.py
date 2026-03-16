from dal import update_user_currencies, modify_tool_amount, update_tree_height
from config import logger
from config import logger, TREE_REWARD_MONEY
class TreeService:
    @staticmethod
    def fertilize(username):
        new_height = update_tree_height(username, height_delta=1)
        update_user_currencies(username, money_delta=TREE_REWARD_MONEY)
        modify_tool_amount(username, tool_id=3008, amount_delta=10)
        logger.info(f"[世界树] {username} 施肥，高度: {new_height}")
        return new_height