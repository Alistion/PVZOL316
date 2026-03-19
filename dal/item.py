# dal/item.py
from .core import get_connection


def get_user_tools(username):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM user_tools WHERE username = ?", (username,)
            ).fetchall()
        ]


def get_tool_amount(username, tool_id):
    """返回指定道具的当前数量，不存在则返回 0"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT amount FROM user_tools WHERE username = ? AND tool_id = ?",
            (username, tool_id),
        ).fetchone()
        return row["amount"] if row else 0


def modify_tool_amount(username, tool_id, amount_delta):
    """增减道具数量；数量归零时自动删除行；返回操作是否实际执行"""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT amount FROM user_tools WHERE username = ? AND tool_id = ?",
            (username, tool_id),
        ).fetchone()
        if existing:
            new_amount = existing["amount"] + amount_delta
            if new_amount > 0:
                conn.execute(
                    "UPDATE user_tools SET amount = ? WHERE username = ? AND tool_id = ?",
                    (new_amount, username, tool_id),
                )
            else:
                conn.execute(
                    "DELETE FROM user_tools WHERE username = ? AND tool_id = ?",
                    (username, tool_id),
                )
        elif amount_delta > 0:
            conn.execute(
                "INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)",
                (username, tool_id, amount_delta),
            )
        conn.commit()
        return True


def set_tool_amount(username, tool_id, amount):
    """直接将道具数量设置为指定值（amount<=0 时删除该行）"""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM user_tools WHERE username = ? AND tool_id = ?",
            (username, tool_id),
        ).fetchone()
        if amount <= 0:
            conn.execute(
                "DELETE FROM user_tools WHERE username = ? AND tool_id = ?",
                (username, tool_id),
            )
        elif existing:
            conn.execute(
                "UPDATE user_tools SET amount = ? WHERE username = ? AND tool_id = ?",
                (amount, username, tool_id),
            )
        else:
            conn.execute(
                "INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)",
                (username, tool_id, amount),
            )
        conn.commit()


def consume_tool(username, tool_id, amount=1):
    """
    扣减道具库存。
    成功返回 True，道具数量不足则返回 False（不操作数据库）。
    """
    current = get_tool_amount(username, tool_id)
    if current < amount:
        return False
    modify_tool_amount(username, tool_id, -amount)
    return True
