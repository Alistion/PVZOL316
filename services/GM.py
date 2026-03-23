# services/GM.py
from config import logger
from dal import (
    clear_organisms,
    clone_user_data,
    delete_organism_by_id,
    delete_user,
    get_username_by_uid,
    modify_tool_amount,
    reset_tree_gm,
    set_tool_amount,
    update_user_data,
    update_user_gm,
)


class GMService:
    @staticmethod
    def handle_post(form):
        """处理 GM 用户列表页的表单提交（克隆等全局操作）"""
        action = form.get("action")

        # ── 账号克隆 ──
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

        # ── 常规单号操作（保留向后兼容）──
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
    def handle_user_detail_post(username, form):
        """
        处理用户详情页的所有 POST 操作。
        返回 True 表示账号已被删除，调用方应跳转回用户列表；
        返回 False 表示留在当前详情页。
        """
        action = form.get("action")

        # ── 保存基础属性 ──────────────────────────────────────────────────────
        if action == "update_info":
            fields = {}
            int_fields = [
                "money",
                "rmb_money",
                "level",
                "honor",
                "merit",
                "gift_ticket",
                "tree_height",
                "tree_times",
            ]
            for field in int_fields:
                val = form.get(field)
                if val is not None and val != "":
                    try:
                        fields[field] = int(val)
                    except ValueError:
                        pass

            arena = form.get("arena_lineup", "").strip()
            if arena != "":
                fields["arena_lineup"] = arena

            if fields:
                update_user_data(username, **fields)
                logger.info(f"[GM] 更新属性：{username} → {fields}")

        # ── 设置道具数量 ──────────────────────────────────────────────────────
        elif action == "set_tool":
            try:
                tool_id = int(form.get("tool_id", 0))
                amount = int(form.get("amount", 0))
                if tool_id:
                    set_tool_amount(username, tool_id, amount)
                    logger.info(f"[GM] 设置道具：{username} ID:{tool_id} → {amount}")
            except ValueError:
                pass

        # ── 新增道具 ──────────────────────────────────────────────────────────
        elif action == "add_tool":
            try:
                tool_id = int(form.get("tool_id", 0))
                amount = int(form.get("amount", 0))
                if tool_id and amount > 0:
                    modify_tool_amount(username, tool_id, amount)
                    logger.info(f"[GM] 新增道具：{username} ID:{tool_id} x{amount}")
            except ValueError:
                pass

        # ── 删除单个道具 ──────────────────────────────────────────────────────
        elif action == "del_tool":
            try:
                tool_id = int(form.get("tool_id", 0))
                if tool_id:
                    set_tool_amount(username, tool_id, 0)
                    logger.info(f"[GM] 删除道具：{username} ID:{tool_id}")
            except ValueError:
                pass

        # ── 删除单个植物 ──────────────────────────────────────────────────────
        elif action == "del_org":
            try:
                org_id = int(form.get("org_id", 0))
                if org_id:
                    delete_organism_by_id(username, org_id)
                    logger.info(f"[GM] 删除植物：{username} 植物ID:{org_id}")
            except ValueError:
                pass

        # ── 清空所有植物 ──────────────────────────────────────────────────────
        elif action == "clear_orgs":
            clear_organisms(username)
            logger.info(f"[GM] 清空所有植物：{username}")

        # ── 重置世界树 ────────────────────────────────────────────────────────
        elif action == "reset_tree":
            reset_tree_gm(username)
            logger.info(f"[GM] 重置世界树：{username}")

        # ── 删除账号（需要跳转回列表页）─────────────────────────────────────
        elif action == "delete_user":
            delete_user(username)
            logger.info(f"[GM] 删除账号：{username}")
            return True  # ← 告诉调用方跳转到 /gm

        return False

    @staticmethod
    def handle_software_api(form):
        """
        外部软件/脚本调用的 GM API 入口（POST /api/gm_software）。
        目前为占位实现，后续按需扩展。
        """
        action = form.get("action", "")
        logger.warning(f"[GM Software API] 收到未实现的动作: {action!r}")
        return f"action '{action}' not implemented", 501
