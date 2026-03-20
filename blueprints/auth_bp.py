# blueprints/auth_bp.py
from flask import Blueprint, redirect, render_template, request, session

from dal import get_or_create_user, register_user, update_avatar, verify_user
from services import AuthService
from blueprints.game_bp import process_amf_request
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Flash 发来的 AMF 裸 POST（无 form 数据）
        if not request.form:
            

            return process_amf_request(session.get("username", "TL"))

        if request.form.get("action") == "login":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                return render_template(
                    "login.html", msg="账号和密码不能为空！", is_success=False
                )

            success, msg = verify_user(username, password)
            if success:
                session["username"] = username
                user_data = get_or_create_user(username)
                session["uid"] = user_data["id"] + 100000
                return redirect("/game")
            else:
                return render_template("login.html", msg=msg, is_success=False)

    # GET 请求：已登录则跳游戏页，否则清空残缺 session 并显示登录页
    if "username" in session and "uid" in session:
        return redirect("/game")

    session.clear()
    return render_template("login.html", msg="", is_success=False)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form.get("action") == "register":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                return render_template(
                    "register.html", msg="账号和密码不能为空！", is_success=False
                )

            success, msg, uid = register_user(username, password)

            if success:
                avatar_url = AuthService.process_avatar_upload(
                    uid, request.files.get("avatar")
                )
                if avatar_url != "/pvz/avatar/1.png":
                    update_avatar(uid, avatar_url)
                return render_template("login.html", msg=msg, is_success=True)
            else:
                return render_template("register.html", msg=msg, is_success=False)

    return render_template("register.html", msg="", is_success=False)


@auth_bp.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("uid", None)
    return redirect("/")
