# dal.py
import sqlite3
import json
from config import logger, DB_FILE, DEFAULT_MONEY, DEFAULT_RMB, DEFAULT_LEVEL
'''数据库管理'''
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
            
            # 兼容旧数据库的字段热更新
            try:
                conn.execute('ALTER TABLE users ADD COLUMN tree_height INTEGER DEFAULT 0')
                conn.execute('ALTER TABLE users ADD COLUMN tree_times INTEGER DEFAULT 9999')
            except sqlite3.OperationalError:
                pass
            # 自动给老玩家增加新货币钱包
            try:
                conn.execute('ALTER TABLE users ADD COLUMN honor INTEGER DEFAULT 0')
                conn.execute('ALTER TABLE users ADD COLUMN merit INTEGER DEFAULT 0')
                conn.execute('ALTER TABLE users ADD COLUMN gift_ticket INTEGER DEFAULT 0')
            except sqlite3.OperationalError: pass

        logger.info("数据库初始化完成，表结构已就绪。")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

# ================= 基础 CRUD =================
def get_all_users():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM users').fetchall()]

def get_or_create_user(username):
    with get_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            conn.execute('INSERT INTO users (username) VALUES (?)', (username,))
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        return dict(user)

def update_user_gm(username, money, rmb, level):
    with get_connection() as conn:
        conn.execute('UPDATE users SET money=?, rmb_money=?, level=? WHERE username=?', (money, rmb, level, username))
        conn.commit()

# 升级加减钱的万能引擎，加入三种新货币的参数
def update_user_currencies(username, money_delta=0, rmb_delta=0, honor_delta=0):
    with get_connection() as conn:
        conn.execute('''UPDATE users 
                        SET money = money + ?, 
                            rmb_money = rmb_money + ?,
                            honor = honor + ?
                        WHERE username = ?''', 
                     (money_delta, rmb_delta, honor_delta, username))
        conn.commit()
        # 【重要修复】改成 SELECT * ，把荣誉等所有最新信息都提取出来
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        return dict(row)

def update_tree_height(username, height_delta):
    with get_connection() as conn:
        conn.execute('UPDATE users SET tree_height = tree_height + ? WHERE username = ?', (height_delta, username))
        conn.commit()
        return conn.execute('SELECT tree_height FROM users WHERE username = ?', (username,)).fetchone()['tree_height']

def reset_tree_gm(username):
    with get_connection() as conn:
        conn.execute('UPDATE users SET tree_height=0, tree_times=9999 WHERE username=?', (username,))
        conn.commit()

# ================= 道具系统 =================
def get_user_tools(username):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM user_tools WHERE username = ?', (username,)).fetchall()]

def modify_tool_amount(username, tool_id, amount_delta):
    with get_connection() as conn:
        existing = conn.execute('SELECT amount FROM user_tools WHERE username=? AND tool_id=?', (username, tool_id)).fetchone()
        if existing:
            new_amount = existing['amount'] + amount_delta
            if new_amount > 0:
                conn.execute('UPDATE user_tools SET amount = ? WHERE username=? AND tool_id=?', (new_amount, username, tool_id))
            else:
                conn.execute('DELETE FROM user_tools WHERE username=? AND tool_id=?', (username, tool_id))
        elif amount_delta > 0:
            conn.execute('INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)', (username, tool_id, amount_delta))
        conn.commit()
        return True

# ================= 生物(植物)系统 =================
def get_user_organisms(username):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM user_organisms WHERE username = ?', (username,)).fetchall()]

def add_organism(username, pid, data_dict):
    with get_connection() as conn:
        conn.execute('INSERT INTO user_organisms (username, pid, data) VALUES (?, ?, ?)', (username, pid, json.dumps(data_dict)))
        conn.commit()

def clear_organisms(username):
    with get_connection() as conn:
        conn.execute('DELETE FROM user_organisms WHERE username=?', (username,))
        conn.commit()

