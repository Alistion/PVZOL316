# server.py
import os
import pyamf
from pyamf import remoting
from flask import Flask, send_from_directory, request, Response, session, render_template_string

# 引入重构后的模块
from config import logger, SECRET_KEY, MASTER_KEY_XML
from dal import init_db, get_all_users
from services import GMService
from api_xml import build_user_xml, build_warehouse_xml, handle_tree_fertilize
from api_amf import route_amf_logic

app = Flask(__name__)
app.secret_key = SECRET_KEY

# 初始化数据库
init_db()

# ================= GM 上帝控制台页面 (内联 HTML 防止依赖外部文件) =================
def render_gm_html(users):
    html = """<!DOCTYPE html><html><head><title>PvZ - GM 控制台</title><style>body{background:#222;color:#0f0;font-family:monospace;padding:20px;} table{border-collapse:collapse;width:100%;margin-bottom:30px;} th,td{border:1px solid #0f0;padding:10px;text-align:center;} input{background:#111;color:#0f0;border:1px solid #0f0;padding:5px;} button{background:#0f0;color:#000;padding:5px 15px;cursor:pointer;font-weight:bold; border-radius:5px;} .panel{border:1px solid #0f0; padding:20px; display:inline-block; margin-right:20px; vertical-align:top; margin-bottom:20px;} .grid-form{display:flex; flex-wrap:wrap; gap:10px; align-items:center;} .grid-item{width: 48%;}</style></head><body><h1>🛠️ GM 控制台</h1><a href="/" style="color:#fff;">[返回游戏]</a><hr>
    <h3>1. 角色属性管理</h3><table><tr><th>角色名</th><th>金币</th><th>金券</th><th>等级</th><th>操作</th><th>急救</th></tr>"""
    for u in users:
        html += f"""<tr><form method="POST" action="/gm"><input type="hidden" name="action" value="update_user"><td><input type="hidden" name="username" value="{u['username']}">{u['username']}</td><td><input type="number" name="money" value="{u['money']}" style="width:100px;"></td><td><input type="number" name="rmb_money" value="{u['rmb_money']}" style="width:100px;"></td><td><input type="number" name="level" value="{u['level']}" style="width:100px;"></td><td><button type="submit">保存</button></td></form><form method="POST" action="/gm" style="display:inline;"><input type="hidden" name="action" value="clear_orgs"><input type="hidden" name="username" value="{u['username']}"><td><button type="submit" style="background:#f00; color:#fff;">清空植物</button></td></form></tr>"""
    
    html += """</table>
    <div class="panel"><h3>2. 物品发送</h3><form method="POST" action="/gm"><input type="hidden" name="action" value="add_tool">玩家: <input type="text" name="username" style="width:120px;" required><br><br>道具ID: <input type="number" name="tool_id" style="width:120px;" required><br><br>数量: <input type="number" name="amount" value="99" style="width:120px;" required><br><br><button type="submit" style="width:100%;">确认发送</button></form></div>
    <div class="panel" style="border-color:#0ff; max-width: 550px;"><h3 style="color:#0ff;">3. 终极神宠定制</h3><form method="POST" action="/gm" class="grid-form"><input type="hidden" name="action" value="add_plant"><div class="grid-item">玩家: <input type="text" name="username" style="width:100px;" required></div><div class="grid-item">植物ID: <input type="number" name="pid" value="771" style="width:70px;" required></div><button type="submit" style="width:100%; background:#0ff; color:#000; padding:10px; margin-top:10px;">⚡ 创造破界神宠 ⚡</button></form></div>
    <div class="panel" style="border-color:#ff0;"><h3 style="color:#ff0;">4. 世界之树</h3><form method="POST" action="/gm"><input type="hidden" name="action" value="reset_tree">玩家: <input type="text" name="username" style="width:120px;" required><br><br><button type="submit" style="width:100%; background:#ff0; color:#000;">🌲 重置高度 🌲</button></form></div></body></html>"""
    return html

@app.route('/gm', methods=['GET', 'POST'])
def gm_panel():
    if request.method == 'POST':
        GMService.handle_post(request.form)
    users = get_all_users()
    return render_template_string(render_gm_html(users))

@app.route('/api/gm_software', methods=['POST'])
def api_gm_software():
    """这是给本地 GM 软件专用的通信接口"""
    # 1. 独立的安全密码校验，防止被黑客恶意刷物品
    gm_password = request.form.get('password')
    if gm_password != "niubi666":  # 改成你自己想要的 GM 软件独立密码
        return "密码错误，拒绝访问！", 403
        
    action = request.form.get('action')
    username = request.form.get('username')
    
    if not username:
        return "玩家账号不能为空！", 400
        
    try:
        if action == 'send_tool':
            tool_id = int(request.form.get('tool_id', 0))
            amount = int(request.form.get('amount', 0))
            from dal import modify_tool_amount
            modify_tool_amount(username, tool_id, amount)
            return f"成功给 {username} 发送了道具ID: {tool_id} 共 {amount} 个！", 200
            
        elif action == 'add_money':
            money = int(request.form.get('money', 0))
            rmb = int(request.form.get('rmb', 0))
            honor = int(request.form.get('honor', 0))
            merit = int(request.form.get('merit', 0))
            ticket = int(request.form.get('ticket', 0))
            
            from dal import update_user_currencies, modify_tool_amount
            # 兼容旧版本防报错
            try:
                update_user_currencies(username, money_delta=money, rmb_delta=rmb, honor_delta=honor, merit_delta=merit, ticket_delta=ticket)
            except TypeError:
                update_user_currencies(username, money_delta=money, rmb_delta=rmb)
            
            # 【核心补丁】发实体道具！
            # 850 是功勋牌，1 是礼券
            if merit > 0: 
                modify_tool_amount(username, tool_id=850, amount_delta=merit)
            if ticket > 0: 
                modify_tool_amount(username, tool_id=1, amount_delta=ticket)
            
            return f"成功给 {username} 充值了...", 200
        # 【新增】清零货币的急救通道
        elif action == 'clear_money':
            from dal import reset_user_currencies
            reset_user_currencies(username)
            return f"急救成功！已将 {username} 的所有货币归零！快去登录游戏试试！", 200
        
        elif action == 'clear_plant':
            from dal import clear_organisms
            clear_organisms(username)
            return f"已成功清空 {username} 的所有植物！", 200
            
        return "未知的操作指令", 400
    except Exception as e:
        logger.error(f"GM 软件操作失败: {e}")
        return f"服务器内部错误: {e}", 500
# ================= 协议解析入口 =================
def process_amf_request():
    try:
        req_data = request.get_data()
        if not req_data: return Response(MASTER_KEY_XML, mimetype='text/xml')
        req_env = remoting.decode(req_data)
        resp_env = remoting.Envelope(req_env.amfVersion)
        current_user = session.get('username', 'TL')

        for msg_id, req_msg in req_env:
            api_name = getattr(req_msg, 'target', 'unknown')
            # if api_name != "api.message.gets":
            logger.info(f"[AMF 路由] 接口: {api_name}")
            resp_body = route_amf_logic(api_name, req_msg.body, current_user)
            resp_env[msg_id] = remoting.Response(resp_body)
        return Response(remoting.encode(resp_env).getvalue(), mimetype='application/x-amf')
    except Exception as e:
        logger.error(f"AMF 解析崩溃: {e}", exc_info=True)
        return Response(MASTER_KEY_XML, mimetype='text/xml')

# ================= 主路由拦截 =================
@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def index():
    if request.method == 'POST': return process_amf_request()
    username = request.args.get('u', '')
    if 'start' not in request.args:
        return f"""<!DOCTYPE html><html><body style="background:#111;color:#fff;text-align:center;padding-top:100px;"><h1>🌿 PvZ Online</h1><form action="/"><input type="text" name="u" required value="{username}"><input type="hidden" name="start" value="1"><button type="submit">启动</button></form><br><a href="/gm" style="color:#0f0;">GM 控制台</a></body></html>"""
    session['username'] = username
    return f"""<!DOCTYPE html><html><body style="background:#222; text-align:center; color:#eee;"><div>欢迎，<b style="color:#76b900;">{username}</b></div><embed src="/main.swf" width="760" height="600" type="application/x-shockwave-flash" allowscriptaccess="always" flashvars="base_url=http://127.0.0.1:8080/&base_url_info=http://127.0.0.1:8080/"></body></html>"""

@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path=""):
    if request.method == 'POST': return process_amf_request()
    if path == "favicon.ico": return ""
    if "default/isnew" in path: return "0"
    
    current_user = session.get('username', 'TL')
    
    # 派发 XML 业务
    if "default/user" in path: return Response(build_user_xml(current_user), mimetype='text/xml')
    if "Warehouse" in path: return Response(build_warehouse_xml(current_user), content_type='text/xml; charset=utf-8')
    if "tree/addheight" in path: return Response(handle_tree_fertilize(current_user), content_type='text/xml; charset=utf-8')

    # 静态缓存路由
    paths_to_try = [path, os.path.join('cache', 'youkia', path), os.path.join('cache', 'pvz', path), os.path.join('cache', path)]
    for try_path in paths_to_try:
        if os.path.exists(try_path): return send_from_directory(os.path.dirname(try_path) or '.', os.path.basename(try_path))
    
    if path.endswith(('.swf', '.png', '.jpg', '.mp3', '.xml')): return "File Not Found", 404
    return Response(MASTER_KEY_XML, mimetype='text/xml')

if __name__ == '__main__':
    logger.info("🌿 PvZ 私服核心启动于 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080)