# dal/plant.py
import json

from .core import get_connection


def get_user_organisms(username):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM user_organisms WHERE username = ?", (username,)
            ).fetchall()
        ]


def get_organism_by_id(username, org_id):
    """获取单个植物的 JSON 数据字典，找不到返回 None"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT data FROM user_organisms WHERE username = ? AND id = ?",
            (username, org_id),
        ).fetchone()
        return json.loads(row["data"]) if row else None


def update_organism_data(username, org_id, data_dict):
    """将植物数据字典序列化后写回数据库"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE user_organisms SET data = ? WHERE username = ? AND id = ?",
            (json.dumps(data_dict), username, org_id),
        )
        conn.commit()


def delete_organism_by_id(username, org_id):
    """从数据库删除单个植物记录"""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM user_organisms WHERE username = ? AND id = ?",
            (username, org_id),
        )
        conn.commit()


def add_organism(username, pid, data_dict):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO user_organisms (username, pid, data) VALUES (?, ?, ?)",
            (username, pid, json.dumps(data_dict)),
        )
        conn.commit()


def clear_organisms(username):
    with get_connection() as conn:
        conn.execute("DELETE FROM user_organisms WHERE username = ?", (username,))
        conn.commit()
