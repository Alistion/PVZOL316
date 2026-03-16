# config.py
import logging

# ================= 日志标准化 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("PvZ_Server")

# ================= 全局常量 =================
SECRET_KEY = "pvzol_super_secret_key"
MASTER_KEY_XML = '<?xml version="1.0" encoding="UTF-8"?><root><response><status>success</status></response></root>'
DB_FILE = 'pvzol.db'

# 初始数值与经济系统配置
DEFAULT_MONEY = 9999999
DEFAULT_RMB = 99999
DEFAULT_LEVEL = 100
SELL_PRICE_PER_ITEM = 500  
TREE_REWARD_MONEY = 8888
SIGN_REWARD_MONEY = 888