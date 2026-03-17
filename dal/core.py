# dal/core.py
import sqlite3
from config import logger, DB_FILE, DEFAULT_MONEY, DEFAULT_RMB, DEFAULT_LEVEL

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        with get_connection() as conn:
            conn.execute(f'''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
                money INTEGER DEFAULT {DEFAULT_MONEY}, rmb_money INTEGER DEFAULT {DEFAULT_RMB}, level INTEGER DEFAULT {DEFAULT_LEVEL},
                tree_height INTEGER DEFAULT 0, tree_times INTEGER DEFAULT 9999
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS user_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, tool_id INTEGER, amount INTEGER
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS user_organisms (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, pid INTEGER, data TEXT
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS user_friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, friend_uid INTEGER
            )''')

            try:
                conn.execute('ALTER TABLE users ADD COLUMN tree_height INTEGER DEFAULT 0')
                conn.execute('ALTER TABLE users ADD COLUMN tree_times INTEGER DEFAULT 9999')
            except sqlite3.OperationalError: pass
            
            try:
                conn.execute('ALTER TABLE users ADD COLUMN honor INTEGER DEFAULT 0')
                conn.execute('ALTER TABLE users ADD COLUMN merit INTEGER DEFAULT 0')
                conn.execute('ALTER TABLE users ADD COLUMN gift_ticket INTEGER DEFAULT 0')
            except sqlite3.OperationalError: pass

            try: conn.execute('ALTER TABLE users ADD COLUMN arena_lineup TEXT DEFAULT ""')
            except sqlite3.OperationalError: pass
            
            try: conn.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')
            except sqlite3.OperationalError: pass

            try: conn.execute('ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT "/pvz/avatar/1.png"')
            except sqlite3.OperationalError: pass

        logger.info("数据库初始化完成，表结构已就绪。")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")