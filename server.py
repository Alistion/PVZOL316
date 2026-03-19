# server.py
import os
import pyamf
from pyamf import remoting
from flask import Flask, send_from_directory, request, Response, session, render_template_string, redirect

# 引入重构后的模块与服务
from config import logger, SECRET_KEY, MASTER_KEY_XML
from dal import init_db, get_all_users, verify_user, register_user,get_or_create_user
from api_xml import build_user_xml, build_warehouse_xml, handle_tree_fertilize,build_recommend_friends_xml
from api_amf import route_amf_logic
from services import GMService, AuthService, OrganismService

app = Flask(__name__)
app.secret_key = SECRET_KEY

# 初始化数据库
init_db()

# ================= GM 管理路由 =================
@app.route('/gm', methods=['GET', 'POST'])
def gm_panel():
    if request.method == 'POST':
        GMService.handle_post(request.form)
    users = get_all_users()
    return render_template_string(GMService.get_gm_html(users))

@app.route('/api/gm_software', methods=['POST'])
def api_gm_software():
    result, status_code = GMService.handle_software_api(request.form)
    return result, status_code

# ================= 核心：动态游戏请求处理 =================
def process_amf_request(current_user):
    try:
        req_data = request.get_data()
        if not req_data: return Response(MASTER_KEY_XML, mimetype='text/xml')
        req_env = remoting.decode(req_data)
        resp_env = remoting.Envelope(req_env.amfVersion)
        
        for msg_id, req_msg in req_env:
            api_name = getattr(req_msg, 'target', 'unknown')
            resp_body = route_amf_logic(api_name, req_msg.body, current_user)
            resp_env[msg_id] = remoting.Response(resp_body)
        return Response(remoting.encode(resp_env).getvalue(), mimetype='application/x-amf')
    except Exception as e:
        logger.error(f"AMF 解析崩溃: {e}", exc_info=True)
        return Response(MASTER_KEY_XML, mimetype='text/xml')

def handle_game_requests(current_user, path=""):
    if request.method == 'POST' and not request.form: 
        return process_amf_request(current_user)
        
    if path == "favicon.ico": return ""
    if "default/isnew" in path: return "0"
    
    if "default/user" in path: return Response(build_user_xml(current_user), mimetype='text/xml')
    if "Warehouse" in path: return Response(build_warehouse_xml(current_user), content_type='text/xml; charset=utf-8')
    if "tree/addheight" in path: return Response(handle_tree_fertilize(current_user), content_type='text/xml; charset=utf-8')
    if "organism/evolution" in path:
        # URL 示例: organism/evolution/id/35/route/1598/shortcut/2...
        parts = path.split('/')
        try:
            # 动态提取 URL 里的 id 和 route 对应的数字
            id_index = parts.index('id') + 1
            org_db_id = int(parts[id_index])
            
            route_index = parts.index('route') + 1
            route_id = int(parts[route_index]) # 提取出来的比如是 1598
            
            
            result_xml = OrganismService.execute_evolution(current_user, org_db_id, route_id)
            return Response(result_xml, mimetype='text/xml')
            
        except (ValueError, IndexError) as e:
            print(f"[合成屋报错] 解析进化 URL 失败: {e}")
            return Response("<root><response><status>error</status></response></root>", mimetype='text/xml')
    if "user/recommendfriend" in path:return Response(build_recommend_friends_xml(current_user), mimetype='text/xml')
    if "user/addfriend" in path:
        from services import FriendService
        # 尝试看看 Flash 有没有发具体 UID
        target_uid = request.values.get('fuid') or request.values.get('id')
        
        if target_uid:
            FriendService.add_friend(current_user, target_uid)
        else:
            # 如果没传 UID，说明这是一键添加按钮，把推荐列表里的人全加了！
            recs = FriendService.get_recommend_list(current_user)
            for r in recs:
                FriendService.add_friend(current_user, r['uid'])
                
        return Response(MASTER_KEY_XML, mimetype='text/xml')
    
    paths_to_try = [path, os.path.join('cache', 'youkia', path), os.path.join('cache', 'pvz', path), os.path.join('cache', path)]
    for try_path in paths_to_try:
        if os.path.exists(try_path): return send_from_directory(os.path.dirname(try_path) or '.', os.path.basename(try_path))
    
    if path.endswith(('.swf', '.png', '.jpg', '.mp3', '.xml')): return "File Not Found", 404
    return Response(MASTER_KEY_XML, mimetype='text/xml')

    


# ================= 动态玩家专属路由 (使用 UID) =================
@app.route('/u/<int:uid>/', methods=['GET', 'POST', 'OPTIONS'])
def user_root(uid):
    from dal import get_username_by_uid
    # 解析出真实账号，如果乱输 UID 找不到
    username = get_username_by_uid(uid)
    return handle_game_requests(username, "")

@app.route('/u/<int:uid>/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def user_catch_all(uid, path):
    from dal import get_username_by_uid
    username = get_username_by_uid(uid)
    return handle_game_requests(username, path)

# ================= 网页端请求路由 (授权模块) =================
@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def index():
    if request.method == 'POST':
        if not request.form: return process_amf_request(session.get('username', 'TL'))
        
        if request.form.get('action') == 'login':
            username, password = request.form.get('username', '').strip(), request.form.get('password', '').strip()
            if not username or not password: 
                return render_template_string(AuthService.get_login_html("账号和密码不能为空！", False))
            
            success, msg = verify_user(username, password)
            if success:
                session['username'] = username
                # 登录成功后，立刻获取数据库 ID 并生成 6 位 UID！
                from dal import get_or_create_user
                user_data = get_or_create_user(username)
                session['uid'] = user_data['id'] + 100000
                return redirect('/game')
            else: 
                return render_template_string(AuthService.get_login_html(msg, False))

    # 【核心修复】：不仅要检查 username，还要同时检查 uid。
    # 如果发现是旧版本残留的残缺缓存，直接强制清空！
    if 'username' in session and 'uid' in session: 
        return redirect('/game')
    else:
        session.clear() # 扫地出门，清除残缺旧缓存
        
    return render_template_string(AuthService.get_login_html())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.form.get('action') == 'register':
            username, password = request.form.get('username', '').strip(), request.form.get('password', '').strip()
            if not username or not password:
                return render_template_string(AuthService.get_register_html("账号和密码不能为空！", False))
            
            # 【流程调整】先在数据库注册生成账号，拿到 UID
            from dal import register_user, update_avatar
            success, msg, uid = register_user(username, password)
            
            if success:
                # 只有注册成功后，才将裁剪好的图片以 UID 命名并保存到本地
                avatar_url = AuthService.process_avatar_upload(uid, request.files.get('avatar'))
                
                # 如果用户传了新图片，再把这个新的 URL (如 /pvz/avatar/100001.png) 写回数据库
                if avatar_url != "/pvz/avatar/1.png":
                    update_avatar(uid, avatar_url)
                    
                return render_template_string(AuthService.get_login_html(msg, True))
            else:
                # 如果账号被占用，直接驳回，不仅不会报错，而且还不会产生垃圾图片文件！
                return render_template_string(AuthService.get_register_html(msg, False))

    return render_template_string(AuthService.get_register_html())

@app.route('/game')
def game():
    username = session.get('username')
    uid = session.get('uid')
    # 【核心修复】：如果没有拿到 uid，也强制清空缓存并退回主页
    if not username or not uid: 
        session.clear()
        return redirect('/')
        
    host_url = request.host_url
    custom_base = f"{host_url}u/{uid}/"
    
    return f"""<!DOCTYPE html><html>
    <head>
        <title>植物大战僵尸Online - 私服</title>
        <script>
            // 【核心劫持魔法】埋伏在这里，专门等 Flash 来调用！
            function gotoFriendPage() {{
                // 1. 拦截指令，弹出私服专属的 UID 输入框
                var targetUid = prompt("👑 \\n请输入你想添加的好友 UID（例如：100002）：");
                
                // 2. 如果玩家输入了 UID 并点击确定
                if (targetUid) {{
                    // 3. 悄悄发送 Ajax 请求给 Python 后端，强制执行双向添加
                    fetch('/api/gm_force_add_friend?target=' + targetUid)
                    .then(response => response.text())
                    .then(text => {{
                        if(text === "OK") {{
                            alert("✅ 添加成功！\\n请刷新游戏网页！");
                        }} else {{
                            alert("❌ 添加失败：" + text);
                        }}
                    }});
                }}
            }}
        </script>
    </head>
    <body style="background:#222; text-align:center; color:#eee; font-family:sans-serif; margin:0; padding-top:20px;">
        <div style="margin-bottom:10px;">欢迎，<b style="color:#76b900;">{username} (UID: {uid})</b> &nbsp;&nbsp;|&nbsp;&nbsp; <a href="/logout" style="color:#ff4444;text-decoration:none;font-weight:bold;">🚪 退出登录</a></div>
        <embed src="/main.swf" width="760" height="600" type="application/x-shockwave-flash" allowscriptaccess="always" flashvars="base_url={custom_base}&base_url_info={custom_base}">
    </body></html>"""
@app.route('/logout')
def logout():
    session.pop('username', None) 
    return redirect('/')

@app.route('/api/gm_force_add_friend', methods=['GET', 'POST'])
def gm_force_add_friend():
    username = session.get('username')
    target_uid = request.values.get('target')
    
    if not username:
        return "未注册", 403
    if not target_uid or not target_uid.isdigit():
        return "无效的 UID", 400
        
    from services import FriendService
    # 调用我们之前在 dal/friend.py 里的双向奔赴逻辑
    FriendService.add_friend(username, target_uid)
    
    return "OK", 200

@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path=""):
    return handle_game_requests(session.get('username', 'TL'), path)

if __name__ == '__main__':
    logger.info("🌿 PvZ 私服核心启动于 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080)