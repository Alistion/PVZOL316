# blueprints/gm_bp.py
import json
import os
import xml.etree.ElementTree as ET

from flask import Blueprint, redirect, render_template, request

from dal import (
    get_all_users,
    get_arena_lineup,
    get_or_create_user,
    get_user_organisms,
    get_user_tools,
    get_username_by_uid,
)
from services import GMService

gm_bp = Blueprint("gm", __name__)


# ── 道具名称缓存（从 tool.xml 解析） ─────────────────────────────────────────

_TOOL_NAMES: dict[int, str] = {}
_ORG_NAMES: dict[int, str] = {}


def _load_tool_names() -> dict[int, str]:
    names: dict[int, str] = {}
    xml_path = os.path.join("cache", "pvz", "php_xml", "tool.xml")
    try:
        tree = ET.parse(xml_path)
        for item in tree.getroot().findall(".//item"):
            tid = item.get("id")
            name = item.get("name", "")
            if tid:
                names[int(tid)] = name
    except Exception:
        pass
    return names


def _load_org_names() -> dict[int, str]:
    names: dict[int, str] = {}
    xml_path = os.path.join("cache", "pvz", "php_xml", "organism.xml")
    try:
        tree = ET.parse(xml_path)
        for item in tree.getroot().findall(".//organisms/item"):
            oid = item.get("id")
            name = item.get("name", "")
            if oid:
                names[int(oid)] = name
    except Exception:
        pass
    return names


# 模块加载时各解析一次，之后直接查内存
_TOOL_NAMES = _load_tool_names()
_ORG_NAMES = _load_org_names()


# ── 路由 ──────────────────────────────────────────────────────────────────────


@gm_bp.route("/gm", methods=["GET", "POST"])
def gm_panel():
    if request.method == "POST":
        GMService.handle_post(request.form)
    users = get_all_users()
    return render_template("gm.html", users=users)


@gm_bp.route("/gm/user/<int:uid>", methods=["GET", "POST"])
def gm_user_detail(uid):
    username = get_username_by_uid(uid)
    if not username:
        return redirect("/gm")

    if request.method == "POST":
        deleted = GMService.handle_user_detail_post(username, request.form)
        if deleted:
            return redirect("/gm")
        return redirect(f"/gm/user/{uid}")

    # ── 组装模板所需数据 ──────────────────────────────────────────────────────

    user = get_or_create_user(username)

    # 道具列表，按 tool_id 升序，附带名称
    raw_tools = sorted(get_user_tools(username), key=lambda t: t["tool_id"])
    tools = [
        {
            "tool_id": t["tool_id"],
            "name": _TOOL_NAMES.get(t["tool_id"], ""),
            "amount": t["amount"],
        }
        for t in raw_tools
    ]

    # 植物列表，解析 JSON data，附带名称
    organisms = []
    for o in get_user_organisms(username):
        try:
            d = json.loads(o["data"])
            order_id = d.get("orderId", 0)
            organisms.append(
                {
                    "id": o["id"],
                    "orderId": order_id,
                    "name": _ORG_NAMES.get(order_id, f"ID:{order_id}"),
                    "grade": d.get("grade", "?"),
                    "quality": d.get("quality_name", "?"),
                    "attack": d.get("attack", 0),
                    "hp_max": d.get("hp_max", 0),
                    "fighting": d.get("fighting", 0),
                }
            )
        except Exception:
            pass

    arena_lineup = get_arena_lineup(username)

    return render_template(
        "gm_user.html",
        user=user,
        uid=uid,
        tools=tools,
        organisms=organisms,
        arena_lineup=arena_lineup,
    )


@gm_bp.route("/api/gm_software", methods=["POST"])
def api_gm_software():
    result, status_code = GMService.handle_software_api(request.form)
    return result, status_code
