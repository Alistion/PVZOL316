# db.py
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('pvzol.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
        money INTEGER DEFAULT 9999999, rmb_money INTEGER DEFAULT 99999, level INTEGER DEFAULT 100
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS user_tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, tool_id INTEGER, amount INTEGER
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS user_organisms (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, pid INTEGER, data TEXT
    )''')
    
    # 数据库字段热更新
    try:
        conn.execute('ALTER TABLE users ADD COLUMN tree_height INTEGER DEFAULT 0')
        conn.execute('ALTER TABLE users ADD COLUMN tree_times INTEGER DEFAULT 9999')
    except Exception:
        pass

    conn.commit()
    conn.close()