# services/Auth.py
import os

class AuthService:
    @staticmethod
    def get_login_html(msg="", is_success=False):
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

    @staticmethod
    def get_register_html(msg="", is_success=False):
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
            avatarInput.addEventListener('change', function(e) {{
                const file = e.target.files[0];
                if (file) {{
                    imageToCrop.src = URL.createObjectURL(file);
                    cropperContainer.style.display = 'block';
                    previewContainer.style.display = 'none';
                    if (cropper) cropper.destroy();
                    imageToCrop.onload = function() {{
                        cropper = new Cropper(imageToCrop, {{ aspectRatio: 1, viewMode: 1, autoCropArea: 0.8 }});
                    }};
                }}
            }});
            cropButton.addEventListener('click', function() {{
                if (!cropper) return;
                const canvas = cropper.getCroppedCanvas({{ width: 256, height: 256, imageSmoothingEnabled: true, imageSmoothingQuality: 'high' }});
                croppedPreview.src = canvas.toDataURL('image/png');
                previewContainer.style.display = 'block';
                cropperContainer.style.display = 'none';
                canvas.toBlob(function(blob) {{
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(new File([blob], "avatar.png", {{ type: "image/png" }}));
                    avatarInput.files = dataTransfer.files; 
                }}, 'image/png');
            }});
          </script>
       </body>
    </html>"""

    @staticmethod
    def process_avatar_upload(uid, avatar_file):
        """处理头像上传逻辑并返回 URL"""
        avatar_url = "/pvz/avatar/1.png" 
        if avatar_file and avatar_file.filename:
            save_dir = os.path.join('cache', 'pvz', 'avatar')
            os.makedirs(save_dir, exist_ok=True)
            
            ext = avatar_file.filename.split('.')[-1]
            # 【核心修改】文件名直接变更为 UID，比如 100001.png
            filename = f"{uid}.{ext}"
            
            avatar_file.save(os.path.join(save_dir, filename))
            avatar_url = f"/pvz/avatar/{filename}"
            
        return avatar_url