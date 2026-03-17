# server.py
import os
import pyamf
from pyamf import remoting
from flask import Flask, send_from_directory, request, Response, session, render_template_string, redirect

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

# ================= GM 上帝控制台页面 =================
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
    gm_password = request.form.get('password')
    if gm_password != "niubi666": return "密码错误，拒绝访问！", 403
    action = request.form.get('action')
    username = request.form.get('username')
    if not username: return "玩家账号不能为空！", 400
        
    try:
        if action == 'send_tool':
            tool_id, amount = int(request.form.get('tool_id', 0)), int(request.form.get('amount', 0))
            from dal import modify_tool_amount
            modify_tool_amount(username, tool_id, amount)
            return f"成功给 {username} 发送了道具ID: {tool_id} 共 {amount} 个！", 200
        elif action == 'add_money':
            money, rmb = int(request.form.get('money', 0)), int(request.form.get('rmb', 0))
            honor, merit = int(request.form.get('honor', 0)), int(request.form.get('merit', 0))
            ticket = int(request.form.get('ticket', 0))
            from dal import update_user_currencies, modify_tool_amount
            try: update_user_currencies(username, money_delta=money, rmb_delta=rmb, honor_delta=honor, merit_delta=merit, ticket_delta=ticket)
            except TypeError: update_user_currencies(username, money_delta=money, rmb_delta=rmb)
            if merit > 0: modify_tool_amount(username, tool_id=850, amount_delta=merit)
            if ticket > 0: modify_tool_amount(username, tool_id=1, amount_delta=ticket)
            return f"成功给 {username} 充值了...", 200
        elif action == 'clear_money':
            from dal import reset_user_currencies
            reset_user_currencies(username)
            return f"急救成功！已将 {username} 的所有货币归零！", 200
        elif action == 'clear_plant':
            from dal import clear_organisms
            clear_organisms(username)
            return f"已成功清空 {username} 的所有植物！", 200
        return "未知的操作指令", 400
    except Exception as e: return f"服务器内部错误: {e}", 500

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
    
    # 派发 XML 业务
    if "default/user" in path: return Response(build_user_xml(current_user), mimetype='text/xml')
    if "Warehouse" in path: return Response(build_warehouse_xml(current_user), content_type='text/xml; charset=utf-8')
    if "tree/addheight" in path: return Response(handle_tree_fertilize(current_user), content_type='text/xml; charset=utf-8')

    # 静态资源请求
    paths_to_try = [path, os.path.join('cache', 'youkia', path), os.path.join('cache', 'pvz', path), os.path.join('cache', path)]
    for try_path in paths_to_try:
        if os.path.exists(try_path): return send_from_directory(os.path.dirname(try_path) or '.', os.path.basename(try_path))
    
    if path.endswith(('.swf', '.png', '.jpg', '.mp3', '.xml')): return "File Not Found", 404
    return Response(MASTER_KEY_XML, mimetype='text/xml')

# ================= 动态玩家专属路由 =================
@app.route('/u/<username>/', methods=['GET', 'POST', 'OPTIONS'])
def user_root(username):
    return handle_game_requests(username, "")

@app.route('/u/<username>/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def user_catch_all(username, path):
    return handle_game_requests(username, path)

# ================= 前端模板：登录与注册 =================
def render_login_html(msg="", is_success=False):
    msg_color = "green" if is_success else "red"
    msg_html = f'<div style="color:{msg_color}; margin-bottom:10px; font-weight:bold;">{msg}</div>' if msg else ''
    
    return f"""<!DOCTYPE html>
<html xmlns:tiles="http://www.thymeleaf.org">
   <head>
      <meta charset="UTF-8">
      <title tiles:fragment="title">登录 - PvZ</title>
      <style>
         body {{ font-family: sans-serif; background: #f4f4f4; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
         .container {{ background: #fff; padding: 30px 40px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center; width: 300px; }}
         fieldset {{ border: none; padding: 0; margin: 0; text-align: left; }}
         legend {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center; width: 100%;}}
         label {{ display: block; margin-top: 10px; margin-bottom: 5px; color: #333; }}
         input[type="text"], input[type="password"] {{ width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
         .btn {{ background: #007bff; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; cursor: pointer; font-size: 16px; }}
         .btn:hover {{ background: #0056b3; }}
         h4 a {{ color: #007bff; text-decoration: none; font-weight: normal; }}
         h4 a:hover {{ text-decoration: underline; }}
      </style>
   </head>
   <body>
      <div class="container" tiles:fragment="content">
         <form name="f" action="/" method="post">
            <input type="hidden" name="action" value="login">
            <fieldset>
               <legend>请登录</legend>
               {msg_html}
               <label for="username">账号</label>
               <input type="text" name="username" required/>        
               
               <label for="password">密码</label>
               <input type="password" name="password" required/>
               
               <div class="form-actions">
                  <button type="submit" class="btn">登录</button>
               </div>
            </fieldset>
         </form>
         <div style="margin-top:20px;">
            <h4><a href="/register">新用户注册</a></h4>
            <h4><a href="/gm" target="_blank">GM 控制台</a></h4>
         </div>
      </div>
   </body>
</html>"""

def render_register_html(msg="", is_success=False):
    msg_color = "green" if is_success else "red"
    msg_html = f'<div style="color:{msg_color}; margin-bottom:10px; font-weight:bold;">{msg}</div>' if msg else ''
    
    return f"""<!DOCTYPE html>
<html>
   <head>
      <meta charset="UTF-8">
      <title>用户注册</title>
      <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
      <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
      <style>
         body {{ font-family: sans-serif; background: #f4f4f4; padding-top: 40px; }}
         .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; text-align: left; }}
         h1 {{ font-size: 20px; color: #333; text-align: center; margin-bottom: 20px; }}
         label {{ display: block; margin-bottom: 5px; color: #555; font-weight: bold; }}
         .form-control {{ width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
         .btn-primary {{ background: #007bff; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; margin-top: 10px; }}
         .btn-primary:hover {{ background: #0056b3; }}
         .text-center {{ text-align: center; }}
         h4 a {{ color: #007bff; text-decoration: none; }}
         h4 a:hover {{ text-decoration: underline; }}
         /* 裁剪框保护样式 */
         #imageToCrop {{ display: block; max-width: 100%; }}
      </style>
   </head>
   <body>
      <div class="container">
         <h1><center>用户注册 - 请勿填写真实隐私！</center></h1>
         <div class="text-center">{msg_html}</div>
         
         <form action="/register" method="post" enctype="multipart/form-data" id="regForm">
            <input type="hidden" name="action" value="register">
            <div>
               <label class="username">用户名(2-10字符): </label>
               <input class="form-control" type="text" minlength="2" maxlength="10" name="username" required/>
            </div>
            <div>
               <label class="password">密码(6-32字符): </label>
               <input class="form-control" type="password" minlength="6" maxlength="32" name="password" required/>
            </div>
            
            <div>
               <label style="color:#555;">🖼️ 专属头像 (可选, 支持任意尺寸)</label>
               <input type="file" name="avatar" id="avatarInput" accept="image/png, image/jpeg, image/jpg" style="padding:0; border:none; margin-top:5px; margin-bottom:15px; font-size:14px; width:100%;">
            </div>

            <div id="cropperContainer" style="display:none; margin-bottom: 15px; text-align: center; padding: 10px; background: #f9f9f9; border-radius: 4px;">
                <div style="max-height: 300px; overflow: hidden; margin-bottom: 10px; box-shadow: 0 0 5px rgba(0,0,0,0.2);">
                    <img id="imageToCrop" src="">
                </div>
                <button type="button" id="cropButton" class="btn-primary" style="background: #28a745; width: auto; padding: 8px 20px;">✂️ 确认裁剪并预览</button>
            </div>

            <div id="previewContainer" style="display:none; text-align:center; margin-bottom: 15px;">
                <p style="font-size:12px; color:#28a745; font-weight:bold;">已成功裁剪为 256x256：</p>
                <img id="croppedPreview" src="" style="border: 2px solid #28a745; border-radius: 4px; width: 128px; height: 128px; box-shadow: 0 0 5px rgba(0,0,0,0.2);">
            </div>

            <div>
               <button type="submit" class="btn-primary" id="submitBtn">注册</button> 
            </div>
         </form>
         
         <div class="text-center" style="margin-top:20px;">
            <h4><a href="/">返回主界面</a></h4>
         </div>
      </div>

      <script>
        let cropper = null;
        const avatarInput = document.getElementById('avatarInput');
        const imageToCrop = document.getElementById('imageToCrop');
        const cropperContainer = document.getElementById('cropperContainer');
        const previewContainer = document.getElementById('previewContainer');
        const croppedPreview = document.getElementById('croppedPreview');
        const cropButton = document.getElementById('cropButton');

        // 当用户选择了图片
        avatarInput.addEventListener('change', function(e) {{
            const file = e.target.files[0];
            if (file) {{
                const url = URL.createObjectURL(file);
                imageToCrop.src = url;
                
                // 显示裁剪框，隐藏预览图
                cropperContainer.style.display = 'block';
                previewContainer.style.display = 'none';
                
                // 如果之前有裁剪器，先销毁
                if (cropper) {{
                    cropper.destroy();
                }}
                
                // 初始化裁剪器，强行锁定 1:1 的正方形比例
                imageToCrop.onload = function() {{
                    cropper = new Cropper(imageToCrop, {{
                        aspectRatio: 1, 
                        viewMode: 1,    // 限制裁剪框不能超出图片范围
                        autoCropArea: 0.8,
                    }});
                }};
            }}
        }});

        // 当用户点击“确认裁剪”
        cropButton.addEventListener('click', function() {{
            if (!cropper) return;
            
            // 核心黑科技：直接要求 cropper 吐出一张完美的 256x256 画布！
            const canvas = cropper.getCroppedCanvas({{
                width: 256,
                height: 256,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high',
            }});
            
            // 将画布显示到预览图上
            croppedPreview.src = canvas.toDataURL('image/png');
            previewContainer.style.display = 'block';
            cropperContainer.style.display = 'none';
            
            // 最重要的一步：将画布转换回真实的 File 文件，并神不知鬼不觉地替换掉原本的 input 里的文件！
            canvas.toBlob(function(blob) {{
                const dataTransfer = new DataTransfer();
                const newFile = new File([blob], "avatar.png", {{ type: "image/png" }});
                dataTransfer.items.add(newFile);
                avatarInput.files = dataTransfer.files; 
            }}, 'image/png');
        }});
      </script>
   </body>
</html>"""

# ================= 网页端请求路由 =================
@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def index():
    if request.method == 'POST':
        if not request.form: 
            return process_amf_request(session.get('username', 'TL'))
        
        action = request.form.get('action')
        if action == 'login':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if not username or not password: 
                return render_template_string(render_login_html("账号和密码不能为空！", False))
            
            from dal import verify_user
            success, msg = verify_user(username, password)
            if success:
                session['username'] = username
                return redirect('/game')
            else: 
                return render_template_string(render_login_html(msg, False))

    if 'username' in session: return redirect('/game')
    return render_template_string(render_login_html())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'register':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if not username or not password:
                return render_template_string(render_register_html("账号和密码不能为空！", False))
            
            from dal import register_user
            avatar_file, avatar_url = request.files.get('avatar'), "/pvz/avatar/1.png" 
            if avatar_file and avatar_file.filename:
                save_dir = os.path.join('cache', 'pvz', 'avatar')
                os.makedirs(save_dir, exist_ok=True)
                ext = avatar_file.filename.split('.')[-1]
                filename = f"user_{username}.{ext}"
                avatar_file.save(os.path.join(save_dir, filename))
                avatar_url = f"/pvz/avatar/{filename}"
                
            success, msg = register_user(username, password, avatar_url)
            if success:
                return render_template_string(render_login_html(msg, True))
            else:
                return render_template_string(render_register_html(msg, False))

    return render_template_string(render_register_html())

@app.route('/game')
def game():
    username = session.get('username')
    if not username: return redirect('/')
        
    host_url = request.host_url
    custom_base = f"{host_url}u/{username}/"
    
    return f"""<!DOCTYPE html><html><body style="background:#222; text-align:center; color:#eee; font-family:sans-serif; margin:0; padding-top:20px;">
    <div style="margin-bottom:10px;">欢迎，<b style="color:#76b900;">{username}</b> &nbsp;&nbsp;|&nbsp;&nbsp; <a href="/logout" style="color:#ff4444;text-decoration:none;font-weight:bold;">🚪 退出登录</a></div>
    <embed src="/main.swf" width="760" height="600" type="application/x-shockwave-flash" allowscriptaccess="always" flashvars="base_url={custom_base}&base_url_info={custom_base}"></body></html>"""

@app.route('/logout')
def logout():
    session.pop('username', None) 
    return redirect('/')

@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path=""):
    current_user = session.get('username', 'TL')
    return handle_game_requests(current_user, path)

if __name__ == '__main__':
    logger.info("🌿 PvZ 私服核心启动于 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080)