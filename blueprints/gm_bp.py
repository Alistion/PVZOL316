# blueprints/gm_bp.py
from flask import Blueprint, redirect, render_template, request, session

from dal import get_all_users
from services import GMService

gm_bp = Blueprint("gm", __name__)


@gm_bp.route("/gm", methods=["GET", "POST"])
def gm_panel():
    if request.method == "POST":
        GMService.handle_post(request.form)
    users = get_all_users()
    return render_template("gm.html", users=users)


@gm_bp.route("/api/gm_software", methods=["POST"])
def api_gm_software():
    result, status_code = GMService.handle_software_api(request.form)
    return result, status_code
