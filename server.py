# server.py
from flask import Flask

from blueprints.auth_bp import auth_bp
from blueprints.game_bp import game_bp
from blueprints.gm_bp import gm_bp
from config import SECRET_KEY, logger
from dal import init_db

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── 初始化数据库 ──────────────────────────────────────────────────────────────
init_db()

# ── 注册 Blueprint ────────────────────────────────────────────────────────────
#
# 注册顺序即路由优先级：
#   1. gm_bp    —— /gm、/api/gm_software（精确路径，优先注册避免被 catch_all 吃掉）
#   2. auth_bp  —— /、/register、/logout
#   3. game_bp  —— /game、/u/<uid>/...、/<path:path>（最后兜底）
#
app.register_blueprint(gm_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(game_bp)

if __name__ == "__main__":
    logger.info("🌿 PvZ 私服核心启动于 0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080)
