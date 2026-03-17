# dal/arena.py
from .core import get_connection

def update_arena_lineup(username, lineup_str):
    with get_connection() as conn:
        conn.execute('UPDATE users SET arena_lineup = ? WHERE username = ?', (lineup_str, username))
        conn.commit()

def get_arena_lineup(username):
    with get_connection() as conn:
        row = conn.execute('SELECT arena_lineup FROM users WHERE username = ?', (username,)).fetchone()
        if row and row['arena_lineup']: return row['arena_lineup']
        return ""