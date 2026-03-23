# blueprints/game_bp.py
import os

import pyamf
from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from pyamf import remoting

from api_amf import route_amf_logic
from api_xml import (
    build_recommend_friends_xml,
    build_user_xml,
    build_warehouse_xml,
    handle_tree_fertilize,
)
from config import MASTER_KEY_XML, logger
from dal import get_username_by_uid
from services import FriendService, OrganismService

game_bp = Blueprint("game", __name__)


# ── AMF 二进制请求处理器 ──────────────────────────────────────────────────────


def process_amf_request(current_user):
    try:
        req_data = request.get_data()
        if not req_data:
            return Response(MASTER_KEY_XML, mimetype="text/xml")

        req_env = remoting.decode(req_data)
        resp_env = remoting.Envelope(req_env.amfVersion)

        for msg_id, req_msg in req_env:
            api_name = getattr(req_msg, "target", "unknown")
            resp_body = route_amf_logic(api_name, req_msg.body, current_user)
            resp_env[msg_id] = remoting.Response(resp_body)

        return Response(
            remoting.encode(resp_env).getvalue(), mimetype="application/x-amf"
        )
    except Exception as e:
        logger.error(f"AMF 解析崩溃: {e}", exc_info=True)
        return Response(MASTER_KEY_XML, mimetype="text/xml")


# ── XML 路由的独立处理函数 ────────────────────────────────────────────────────


def _handle_evolution(current_user, path):
    """解析进化 URL，例如：organism/evolution/id/35/route/1598/shortcut/2"""
    parts = path.split("/")
    try:
        org_db_id = int(parts[parts.index("id") + 1])
        route_id = int(parts[parts.index("route") + 1])
        result_xml = OrganismService.execute_evolution(
            current_user, org_db_id, route_id
        )
        return Response(result_xml, mimetype="text/xml")
    except (ValueError, IndexError) as e:
        logger.warning(f"[合成屋] 解析进化 URL 失败: {e}")
        return Response(
            "<root><response><status>error</status></response></root>",
            mimetype="text/xml",
        )


def _handle_add_friend(current_user, path):
    target_uid = request.values.get("fuid") or request.values.get("id")
    if target_uid:
        FriendService.add_friend(current_user, target_uid)
    else:
        # 没传 UID → 一键添加推荐列表里的所有人
        for rec in FriendService.get_recommend_list(current_user):
            FriendService.add_friend(current_user, rec["uid"])
    return Response(MASTER_KEY_XML, mimetype="text/xml")


# ── XML 路由分发表 ────────────────────────────────────────────────────────────
#
# 格式：(路径子串, handler(current_user, path) -> Response)
# 按顺序匹配，找到第一个命中的就执行，不再继续。
#
_XML_ROUTES = [
    (
        "default/isnew",
        lambda u, p: "0",
    ),
    (
        "default/user",
        lambda u, p: Response(build_user_xml(u), mimetype="text/xml"),
    ),
    (
        "Warehouse",
        lambda u, p: Response(
            build_warehouse_xml(u), content_type="text/xml; charset=utf-8"
        ),
    ),
    (
        "tree/addheight",
        lambda u, p: Response(
            handle_tree_fertilize(u), content_type="text/xml; charset=utf-8"
        ),
    ),
    (
        "organism/evolution",
        _handle_evolution,
    ),
    (
        "user/recommendfriend",
        lambda u, p: Response(build_recommend_friends_xml(u), mimetype="text/xml"),
    ),
    (
        "user/addfriend",
        _handle_add_friend,
    ),
]


def _route_xml(current_user, path):
    """依次尝试 XML 路由表，返回 Response 或 None（表示未命中）"""
    for pattern, handler in _XML_ROUTES:
        if pattern in path:
            return handler(current_user, path)
    return None


# ── 统一游戏请求入口 ──────────────────────────────────────────────────────────


def handle_game_requests(current_user, path=""):
    # AMF 二进制 POST（无 form 数据）
    if request.method == "POST" and not request.form:
        return process_amf_request(current_user)

    # 快速跳过无意义路径
    if path == "favicon.ico":
        return ""

    # 尝试 XML 路由表
    xml_response = _route_xml(current_user, path)
    if xml_response is not None:
        return xml_response

    # 静态文件兜底：依次尝试多个可能的磁盘路径
    paths_to_try = [
        path,
        os.path.join("cache", "youkia", path),
        os.path.join("cache", "pvz", path),
        os.path.join("cache", path),
    ]
    for try_path in paths_to_try:
        if os.path.exists(try_path):
            return send_from_directory(
                os.path.dirname(try_path) or ".", os.path.basename(try_path)
            )

    if path.endswith((".swf", ".png", ".jpg", ".mp3", ".xml")):
        return "File Not Found", 404

    # 其他一切未知请求 → 返回通用成功 XML，防止 Flash 报错
    return Response(MASTER_KEY_XML, mimetype="text/xml")


# ── 路由定义 ──────────────────────────────────────────────────────────────────


@game_bp.route("/activity/spin_win")
def serve_spin_win_activity():
    """
    提供活动大转盘网页
    """
    return render_template("activity_spin.html")

@game_bp.route("/game")
def game():
    username = session.get("username")
    uid = session.get("uid")
    if not username or not uid:
        session.clear()
        return redirect("/")

    host_url = request.host_url
    custom_base = f"{host_url}u/{uid}/"

    return render_template(
        "game.html",
        username=username,
        uid=uid,
        custom_base=custom_base,
    )


@game_bp.route("/u/<int:uid>/", methods=["GET", "POST", "OPTIONS"])
def user_root(uid):
    username = get_username_by_uid(uid)
    return handle_game_requests(username, "")


@game_bp.route("/u/<int:uid>/<path:path>", methods=["GET", "POST", "OPTIONS"])
def user_catch_all(uid, path):
    username = get_username_by_uid(uid)
    return handle_game_requests(username, path)


@game_bp.route("/api/gm_force_add_friend", methods=["GET", "POST"])
def gm_force_add_friend():
    username = session.get("username")
    target_uid = request.values.get("target")

    if not username:
        return "未登录", 403
    if not target_uid or not target_uid.isdigit():
        return "无效的 UID", 400

    FriendService.add_friend(username, target_uid)
    return "OK", 200


@game_bp.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def catch_all(path=""):
    return handle_game_requests(session.get("username", "TL"), path)
