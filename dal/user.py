# dal/user.py
import os
import sqlite3
from config import logger
from werkzeug.security import generate_password_hash, check_password_hash
from .core import get_connection

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

def get_username_by_uid(uid):
    try:
        db_id = int(uid) - 100000 
        with get_connection() as conn:
            row = conn.execute('SELECT username FROM users WHERE id = ?', (db_id,)).fetchone()
            if row: return row['username']
    except Exception as e: logger.error(f"UID 解析失败: {e}")
    return None

def register_user(username, password):
    with get_connection() as conn:
        if conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone():
            return False, "账号已被占用，请尝试其他账号或直接登录！", None
        hashed_pw = generate_password_hash(password)
        cursor = conn.execute('INSERT INTO users (username, password, avatar) VALUES (?, ?, "/pvz/avatar/1.png")', (username, hashed_pw))
        uid = cursor.lastrowid + 100000
        conn.commit()
        return True, "注册成功！请点击登录进入游戏。", uid

def verify_user(username, password):
    with get_connection() as conn:
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not row: return False, "该账号不存在，请先注册！"
        user = dict(row)
        db_password = user.get('password', '')
        if not db_password:
            conn.execute('UPDATE users SET password = ? WHERE username = ?', (generate_password_hash(password), username))
            conn.commit()
            return True, "老玩家回归！已自动为您绑定此新密码。"
        if check_password_hash(db_password, password): return True, "登录成功！"
        else: return False, "密码错误，请重试！"

def update_avatar(uid, avatar_url):
    with get_connection() as conn:
        conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_url, uid - 100000))
        conn.commit()

def update_user_gm(username, money, rmb, level):
    with get_connection() as conn:
        conn.execute('UPDATE users SET money=?, rmb_money=?, level=? WHERE username=?', (money, rmb, level, username))
        conn.commit()

def update_user_currencies(username, money_delta=0, rmb_delta=0, honor_delta=0, merit_delta=0, ticket_delta=0):
    with get_connection() as conn:
        try:
            conn.execute('''UPDATE users SET money=money+?, rmb_money=rmb_money+?, honor=honor+?, merit=merit+?, gift_ticket=gift_ticket+? WHERE username=?''', 
                         (money_delta, rmb_delta, honor_delta, merit_delta, ticket_delta, username))
        except sqlite3.OperationalError:
            conn.execute('UPDATE users SET money=money+?, rmb_money=rmb_money+? WHERE username=?', (money_delta, rmb_delta, username))
        conn.commit()
        return dict(conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone())

def reset_user_currencies(username):
    with get_connection() as conn:
        try: conn.execute('UPDATE users SET money=0, rmb_money=0, honor=0, merit=0, gift_ticket=0 WHERE username=?', (username,))
        except sqlite3.OperationalError: conn.execute('UPDATE users SET money=0, rmb_money=0 WHERE username=?', (username,))
        conn.commit()

def update_tree_height(username, height_delta):
    with get_connection() as conn:
        conn.execute('UPDATE users SET tree_height = tree_height + ? WHERE username = ?', (height_delta, username))
        conn.commit()
        return conn.execute('SELECT tree_height FROM users WHERE username = ?', (username,)).fetchone()['tree_height']

def reset_tree_gm(username):
    with get_connection() as conn:
        conn.execute('UPDATE users SET tree_height=0, tree_times=9999 WHERE username=?', (username,))
        conn.commit()

def delete_user(username):
    with get_connection() as conn:
        user = conn.execute('SELECT avatar FROM users WHERE username = ?', (username,)).fetchone()
        if user and user['avatar'] and user['avatar'] != "/pvz/avatar/1.png":
            file_to_delete = os.path.join('cache', *user['avatar'].strip('/').split('/'))
            if os.path.exists(file_to_delete):
                try: os.remove(file_to_delete)
                except Exception: pass
        conn.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.execute('DELETE FROM user_tools WHERE username = ?', (username,))
        conn.execute('DELETE FROM user_organisms WHERE username = ?', (username,))
        conn.commit()

def clone_user_data(source_username, target_username):
    with get_connection() as conn:
        src_user_row = conn.execute('SELECT * FROM users WHERE username=?', (source_username,)).fetchone()
        if not src_user_row: return
        src_user = dict(src_user_row)
        try: conn.execute('UPDATE users SET money=?, rmb_money=?, level=?, honor=?, merit=?, gift_ticket=? WHERE username=?', 
                          (src_user.get('money',0), src_user.get('rmb_money',0), src_user.get('level',100), src_user.get('honor',0), src_user.get('merit',0), src_user.get('gift_ticket',0), target_username))
        except sqlite3.OperationalError: conn.execute('UPDATE users SET money=?, rmb_money=?, level=? WHERE username=?', (src_user.get('money',0), src_user.get('rmb_money',0), src_user.get('level',100), target_username))
        
        conn.execute('DELETE FROM user_tools WHERE username=?', (target_username,))
        conn.execute('DELETE FROM user_organisms WHERE username=?', (target_username,))
        
        src_tools = conn.execute('SELECT tool_id, amount FROM user_tools WHERE username=?', (source_username,)).fetchall()
        for t in src_tools: conn.execute('INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)', (target_username, t['tool_id'], t['amount']))
        
        src_orgs = conn.execute('SELECT pid, data FROM user_organisms WHERE username=?', (source_username,)).fetchall()
        for o in src_orgs: conn.execute('INSERT INTO user_organisms (username, pid, data) VALUES (?, ?, ?)', (target_username, o['pid'], o['data']))
        conn.commit()