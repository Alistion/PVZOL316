# services/GM.py
from config import logger
from dal import (
    clear_organisms,
    clone_user_data,
    delete_user,
    get_username_by_uid,
    modify_tool_amount,
    reset_tree_gm,
    update_user_gm,
)


class GMService:
    @staticmethod
    def handle_post(form):
        """处理 GM 网页端的表单提交"""
        action = form.get("action")

        # ── 账号克隆（需要两个 UID）──
        if action == "clone_user":
            try:
                src_uid = int(form.get("source_uid", 0))
                tgt_uid = int(form.get("target_uid", 0))
            except ValueError:
                return
            src_user = get_username_by_uid(src_uid)
            tgt_user = get_username_by_uid(tgt_uid)
            if src_user and tgt_user and src_user != tgt_user:
                clone_user_data(src_user, tgt_user)
                logger.info(f"[GM] 账号克隆：{src_user} → {tgt_user}")
            return

        # ── 常规单号操作 ──
        uid_str = form.get("uid")
        if not uid_str:
            return
        try:
            uid = int(uid_str)
        except ValueError:
            return

        username = get_username_by_uid(uid)
        if not username:
            return

        if action == "update_user":
            update_user_gm(username, form["money"], form["rmb_money"], form["level"])
            logger.info(f"[GM] 修改属性：{username}")

        elif action == "add_tool":
            modify_tool_amount(username, int(form["tool_id"]), int(form["amount"]))
            logger.info(
                f"[GM] 发送道具 {form['tool_id']} x{form['amount']} → {username}"
            )

        elif action == "clear_orgs":
            clear_organisms(username)
            logger.info(f"[GM] 清空植物：{username}")

        elif action == "reset_tree":
            reset_tree_gm(username)
            logger.info(f"[GM] 重置世界树：{username}")

        elif action == "delete_user":
            delete_user(username)
            logger.info(f"[GM] 删除账号：{username}")

    @staticmethod
    def handle_software_api(form):
        """
        外部软件/脚本调用的 GM API 入口（POST /api/gm_software）。
        目前为占位实现，后续按需扩展。
        """
        action = form.get("action", "")
        logger.warning(f"[GM Software API] 收到未实现的动作: {action!r}")
        return f"action '{action}' not implemented", 501
