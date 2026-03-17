# dal/friend.py
from .core import get_connection

def add_friend_to_db(username, friend_uid):
    """双向奔赴：互相把对方写入好友列表"""
    with get_connection() as conn:
        # 1. 我加你
        existing1 = conn.execute('SELECT * FROM user_friends WHERE username = ? AND friend_uid = ?', (username, friend_uid)).fetchone()
        if not existing1:
            conn.execute('INSERT INTO user_friends (username, friend_uid) VALUES (?, ?)', (username, friend_uid))
        
        # 2. 你加我 (算出我的 uid)
        my_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if my_user:
            my_uid = my_user['id'] + 100000
            # 算出对方的 username
            target_user = conn.execute('SELECT username FROM users WHERE id = ?', (friend_uid - 100000,)).fetchone()
            if target_user:
                target_username = target_user['username']
                existing2 = conn.execute('SELECT * FROM user_friends WHERE username = ? AND friend_uid = ?', (target_username, my_uid)).fetchone()
                if not existing2:
                    conn.execute('INSERT INTO user_friends (username, friend_uid) VALUES (?, ?)', (target_username, my_uid))
        conn.commit()

def get_friend_details(username):
    """联表查询：获取我的所有好友详细信息"""
    with get_connection() as conn:
        sql = '''
            SELECT u.id, u.username, u.level, u.avatar 
            FROM user_friends f
            JOIN users u ON f.friend_uid = (u.id + 100000)
            WHERE f.username = ?
        '''
        return [dict(row) for row in conn.execute(sql, (username,)).fetchall()]