# dal.py
import sqlite3
import json
import os  # <--- 新增这一行用于删除文件
from config import logger, DB_FILE, DEFAULT_MONEY, DEFAULT_RMB, DEFAULT_LEVEL
from werkzeug.security import generate_password_hash, check_password_hash
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

            try:
                conn.execute('ALTER TABLE users ADD COLUMN arena_lineup TEXT DEFAULT ""')
            except sqlite3.OperationalError: pass
            try:
                conn.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')
            except sqlite3.OperationalError: pass

            try:
                conn.execute('ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT "/pvz/avatar/1.png"')
            except sqlite3.OperationalError: pass

        logger.info("数据库初始化完成，表结构已就绪。")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

# ================= 基础 CRUD =================
def get_all_users():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM users').fetchall()]

def delete_user(username):
    """危险操作：彻底删除玩家及其所有关联数据，并清理本地头像缓存"""
    with get_connection() as conn:
        # 1. 查找头像路径并删除物理文件
        user = conn.execute('SELECT avatar FROM users WHERE username = ?', (username,)).fetchone()
        if user and user['avatar']:
            avatar_path = user['avatar']
            if avatar_path != "/pvz/avatar/1.png":
                # 跨平台路径拼接: "/pvz/avatar/100001.png" -> cache/pvz/avatar/100001.png
                parts = avatar_path.strip('/').split('/')
                file_to_delete = os.path.join('cache', *parts)
                if os.path.exists(file_to_delete):
                    try:
                        os.remove(file_to_delete)
                        logger.info(f"[系统] 已清理玩家 {username} 的本地头像文件: {file_to_delete}")
                    except Exception as e:
                        logger.error(f"[系统] 删除头像文件失败: {e}")

        # 2. 删除数据库关联数据
        conn.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.execute('DELETE FROM user_tools WHERE username = ?', (username,))
        conn.execute('DELETE FROM user_organisms WHERE username = ?', (username,))
        conn.commit()
        logger.info(f"[系统] 玩家 {username} 的账号及所有数据已被彻底物理删除！")

def clone_user_data(source_username, target_username):
    """账号克隆大法：将源账号的货币、物品、植物完美复制给目标账号"""
    with get_connection() as conn:
        src_user_row = conn.execute('SELECT * FROM users WHERE username=?', (source_username,)).fetchone()
        if not src_user_row: return
        src_user = dict(src_user_row)
        
        # 1. 覆盖货币、等级
        try:
            conn.execute('''UPDATE users 
                            SET money=?, rmb_money=?, level=?, honor=?, merit=?, gift_ticket=?
                            WHERE username=?''', 
                         (src_user.get('money',0), src_user.get('rmb_money',0), src_user.get('level',100), 
                          src_user.get('honor',0), src_user.get('merit',0), src_user.get('gift_ticket',0), 
                          target_username))
        except sqlite3.OperationalError:
            conn.execute('UPDATE users SET money=?, rmb_money=?, level=? WHERE username=?', 
                         (src_user.get('money',0), src_user.get('rmb_money',0), src_user.get('level',100), target_username))
        
        # 2. 先清空目标账号原有的物品和植物 (防止重复堆叠)
        conn.execute('DELETE FROM user_tools WHERE username=?', (target_username,))
        conn.execute('DELETE FROM user_organisms WHERE username=?', (target_username,))
        
        # 3. 复制背包物品
        src_tools = conn.execute('SELECT tool_id, amount FROM user_tools WHERE username=?', (source_username,)).fetchall()
        for t in src_tools:
            conn.execute('INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)', (target_username, t['tool_id'], t['amount']))
        
        # 4. 复制植物 (连带等级、资质、技能数据原封不动复制)
        src_orgs = conn.execute('SELECT pid, data FROM user_organisms WHERE username=?', (source_username,)).fetchall()
        for o in src_orgs:
            conn.execute('INSERT INTO user_organisms (username, pid, data) VALUES (?, ?, ?)', (target_username, o['pid'], o['data']))
            
        conn.commit()
        
        logger.info(f"[系统] 已成功将玩家 {source_username} 的所有数据克隆给 {target_username}！")
def get_username_by_uid(uid):
    """通过 6 位数字 UID 逆向查找玩家账号名"""
    try:
        # 减去 100000 的偏移量，还原出数据库里的真实 ID
        db_id = int(uid) - 100000 
        with get_connection() as conn:
            row = conn.execute('SELECT username FROM users WHERE id = ?', (db_id,)).fetchone()
            if row:
                return row['username']
    except Exception as e:
        logger.error(f"UID 解析失败: {e}")
    return None

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

# ================= 账号验证系统 =================
def register_user(username, password):
    with get_connection() as conn:
        existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            return False, "账号已被占用，请尝试其他账号或直接登录！", None
        
        from werkzeug.security import generate_password_hash
        hashed_pw = generate_password_hash(password)
        # 写入数据库，暂时分配默认头像 1.png
        cursor = conn.execute('INSERT INTO users (username, password, avatar) VALUES (?, ?, "/pvz/avatar/1.png")', (username, hashed_pw))
        # 核心：立刻获取刚刚插入的数据库主键 ID，并计算出 UID
        uid = cursor.lastrowid + 100000
        conn.commit()
        return True, "注册成功！请点击登录进入游戏。", uid
    
def update_avatar(uid, avatar_url):
    """注册成功后，单独更新头像的路径"""
    db_id = uid - 100000
    with get_connection() as conn:
        conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_url, db_id))
        conn.commit()

def verify_user(username, password):
    with get_connection() as conn:
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not row:
            return False, "该账号不存在，请先注册！"
        
        # 【核心修复】：将 sqlite3.Row 对象转换成真正的 Python 字典！
        user = dict(row)
        
        db_password = user.get('password', '')
        # 兼容老玩家逻辑：如果这是之前的免密老账号，第一次登录时自动绑定当前输入的密码
        if not db_password:
            from werkzeug.security import generate_password_hash
            hashed_pw = generate_password_hash(password)
            conn.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_pw, username))
            conn.commit()
            return True, "老玩家回归！已自动为您绑定此新密码。"
            
        # 校验密码哈希值
        from werkzeug.security import check_password_hash
        if check_password_hash(db_password, password):
            return True, "登录成功！"
        else:
            return False, "密码错误，请重试！"

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

# ================= 斗技场阵容 =================
def update_arena_lineup(username, lineup_str):
    with get_connection() as conn:
        conn.execute('UPDATE users SET arena_lineup = ? WHERE username = ?', (lineup_str, username))
        conn.commit()

def get_arena_lineup(username):
    with get_connection() as conn:
        row = conn.execute('SELECT arena_lineup FROM users WHERE username = ?', (username,)).fetchone()
        if row and row['arena_lineup']:
            return row['arena_lineup']
        return ""