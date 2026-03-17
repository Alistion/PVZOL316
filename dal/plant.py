# dal/plant.py
import json
from .core import get_connection

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