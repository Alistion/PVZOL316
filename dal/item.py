# dal/item.py
from .core import get_connection

def get_user_tools(username):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM user_tools WHERE username = ?', (username,)).fetchall()]

def modify_tool_amount(username, tool_id, amount_delta):
    with get_connection() as conn:
        existing = conn.execute('SELECT amount FROM user_tools WHERE username=? AND tool_id=?', (username, tool_id)).fetchone()
        if existing:
            new_amount = existing['amount'] + amount_delta
            if new_amount > 0: conn.execute('UPDATE user_tools SET amount = ? WHERE username=? AND tool_id=?', (new_amount, username, tool_id))
            else: conn.execute('DELETE FROM user_tools WHERE username=? AND tool_id=?', (username, tool_id))
        elif amount_delta > 0:
            conn.execute('INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)', (username, tool_id, amount_delta))
        conn.commit()
        return True