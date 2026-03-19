# dal/user.py
from __future__ import annotations

import os
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from config import UID_OFFSET, logger

from .core import get_connection


def get_all_users():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM users").fetchall()]


def get_or_create_user(username):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user:
            conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        return dict(user)


def get_username_by_uid(uid):
    try:
        db_id = int(uid) - UID_OFFSET
        with get_connection() as conn:
            row = conn.execute(
                "SELECT username FROM users WHERE id = ?", (db_id,)
            ).fetchone()
            if row:
                return row["username"]
    except Exception as e:
        logger.error(f"UID 解析失败: {e}")
    return None


def register_user(username, password):
    with get_connection() as conn:
        if conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone():
            return False, "账号已被占用，请尝试其他账号或直接登录！", None
        hashed_pw = generate_password_hash(password)
        cursor = conn.execute(
            'INSERT INTO users (username, password, avatar) VALUES (?, ?, "/pvz/avatar/1.png")',
            (username, hashed_pw),
        )
        assert cursor.lastrowid is not None, "INSERT 失败，lastrowid 为 None"
        uid = cursor.lastrowid + UID_OFFSET
        conn.commit()
        return True, "注册成功！请点击登录进入游戏。", uid


def verify_user(username, password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return False, "该账号不存在，请先注册！"
        user = dict(row)
        db_password = user.get("password", "")
        if not db_password:
            conn.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (generate_password_hash(password), username),
            )
            conn.commit()
            return True, "老玩家回归！已自动为您绑定此新密码。"
        if check_password_hash(db_password, password):
            return True, "登录成功！"
        return False, "密码错误，请重试！"


def update_avatar(uid, avatar_url):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET avatar = ? WHERE id = ?",
            (avatar_url, uid - UID_OFFSET),
        )
        conn.commit()


def update_user_gm(username, money, rmb, level):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET money = ?, rmb_money = ?, level = ? WHERE username = ?",
            (money, rmb, level, username),
        )
        conn.commit()


def update_user_currencies(
    username, money_delta=0, rmb_delta=0, honor_delta=0, merit_delta=0, ticket_delta=0
):
    with get_connection() as conn:
        try:
            conn.execute(
                """UPDATE users
                   SET money       = money + ?,
                       rmb_money   = rmb_money + ?,
                       honor       = honor + ?,
                       merit       = merit + ?,
                       gift_ticket = gift_ticket + ?
                   WHERE username = ?""",
                (
                    money_delta,
                    rmb_delta,
                    honor_delta,
                    merit_delta,
                    ticket_delta,
                    username,
                ),
            )
        except sqlite3.OperationalError:
            conn.execute(
                "UPDATE users SET money = money + ?, rmb_money = rmb_money + ? WHERE username = ?",
                (money_delta, rmb_delta, username),
            )
        conn.commit()
        return dict(
            conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        )


def reset_user_currencies(username):
    with get_connection() as conn:
        try:
            conn.execute(
                "UPDATE users SET money = 0, rmb_money = 0, honor = 0, merit = 0, gift_ticket = 0 WHERE username = ?",
                (username,),
            )
        except sqlite3.OperationalError:
            conn.execute(
                "UPDATE users SET money = 0, rmb_money = 0 WHERE username = ?",
                (username,),
            )
        conn.commit()


def update_tree_height(username, height_delta):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tree_height = tree_height + ? WHERE username = ?",
            (height_delta, username),
        )
        conn.commit()
        return conn.execute(
            "SELECT tree_height FROM users WHERE username = ?", (username,)
        ).fetchone()["tree_height"]


def reset_tree_gm(username):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET tree_height = 0, tree_times = 9999 WHERE username = ?",
            (username,),
        )
        conn.commit()


def delete_user(username):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT avatar FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user and user["avatar"] and user["avatar"] != "/pvz/avatar/1.png":
            file_to_delete = os.path.join(
                "cache", *user["avatar"].strip("/").split("/")
            )
            if os.path.exists(file_to_delete):
                try:
                    os.remove(file_to_delete)
                except Exception:
                    pass
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.execute("DELETE FROM user_tools WHERE username = ?", (username,))
        conn.execute("DELETE FROM user_organisms WHERE username = ?", (username,))
        conn.commit()


def clone_user_data(source_username, target_username):
    with get_connection() as conn:
        src_row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (source_username,)
        ).fetchone()
        if not src_row:
            return
        src = dict(src_row)
        try:
            conn.execute(
                """UPDATE users
                   SET money = ?, rmb_money = ?, level = ?,
                       honor = ?, merit = ?, gift_ticket = ?
                   WHERE username = ?""",
                (
                    src.get("money", 0),
                    src.get("rmb_money", 0),
                    src.get("level", 100),
                    src.get("honor", 0),
                    src.get("merit", 0),
                    src.get("gift_ticket", 0),
                    target_username,
                ),
            )
        except sqlite3.OperationalError:
            conn.execute(
                "UPDATE users SET money = ?, rmb_money = ?, level = ? WHERE username = ?",
                (
                    src.get("money", 0),
                    src.get("rmb_money", 0),
                    src.get("level", 100),
                    target_username,
                ),
            )

        conn.execute("DELETE FROM user_tools WHERE username = ?", (target_username,))
        conn.execute(
            "DELETE FROM user_organisms WHERE username = ?", (target_username,)
        )

        for t in conn.execute(
            "SELECT tool_id, amount FROM user_tools WHERE username = ?",
            (source_username,),
        ).fetchall():
            conn.execute(
                "INSERT INTO user_tools (username, tool_id, amount) VALUES (?, ?, ?)",
                (target_username, t["tool_id"], t["amount"]),
            )

        for o in conn.execute(
            "SELECT pid, data FROM user_organisms WHERE username = ?",
            (source_username,),
        ).fetchall():
            conn.execute(
                "INSERT INTO user_organisms (username, pid, data) VALUES (?, ?, ?)",
                (target_username, o["pid"], o["data"]),
            )

        conn.commit()


# 允许通过 update_user_data 修改的字段白名单
_UPDATABLE_FIELDS = frozenset(
    {
        "money",
        "rmb_money",
        "level",
        "honor",
        "merit",
        "gift_ticket",
        "tree_height",
        "tree_times",
        "arena_lineup",
    }
)


def update_user_data(username: str, **fields) -> None:
    """
    更新用户任意字段，白名单保护防止传入非法列名。

    示例：
        update_user_data("Alice", money=99999, level=200)
        update_user_data("Alice", arena_lineup="1,2,3,4")
    """
    safe = {k: v for k, v in fields.items() if k in _UPDATABLE_FIELDS}
    if not safe:
        return
    set_clause = ", ".join(f"{k} = ?" for k in safe)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE users SET {set_clause} WHERE username = ?",
            list(safe.values()) + [username],
        )
        conn.commit()
