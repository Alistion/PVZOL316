# services/GM.py
from dal import update_user_currencies, modify_tool_amount, update_tree_height, clear_organisms, get_all_users, update_user_gm, reset_tree_gm, delete_user, clone_user_data
from config import logger

class GMService:
    @staticmethod
    def get_gm_html(users):
        """返回 GM 网页端的 HTML (现代化亮色主题 + 下拉框 + 克隆功能)"""
        
        # 动态生成所有玩家的下拉选项 (UID - 名字)
        options_html = ""
        for u in users:
            uid = u['id'] + 100000
            options_html += f'<option value="{uid}">{uid} - {u["username"]}</option>'

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PvZ - GM 控制台</title>
    <style>
        body {{ font-family: sans-serif; background: #f4f4f4; padding: 30px; margin: 0; color: #333; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; max-width: 1200px; margin-left: auto; margin-right: auto; }}
        .header h1 {{ margin: 0; color: #333; font-size: 24px; }}
        .header a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
        .header a:hover {{ text-decoration: underline; }}
        .container {{ background: #fff; padding: 20px 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 20px; max-width: 1200px; margin-left: auto; margin-right: auto; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: center; }}
        th {{ background-color: #f8f9fa; font-weight: bold; color: #555; }}
        tr:hover {{ background-color: #f1f7fd; }}
        /* 统一下拉框和输入框的样式 */
        input[type="number"], input[type="text"], select {{ padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; width: 100%; outline: none; transition: border 0.3s; font-size: 14px; background: white; }}
        input:focus, select:focus {{ border-color: #007bff; }}
        .btn {{ border: none; padding: 8px 15px; cursor: pointer; font-weight: bold; border-radius: 4px; color: white; transition: background 0.2s; font-size: 14px; }}
        .btn-primary {{ background: #007bff; }}
        .btn-primary:hover {{ background: #0056b3; }}
        .btn-danger {{ background: #dc3545; }}
        .btn-danger:hover {{ background: #c82333; }}
        .btn-success {{ background: #28a745; }}
        .btn-success:hover {{ background: #218838; }}
        .btn-warning {{ background: #ffc107; color: #212529; }}
        .btn-warning:hover {{ background: #e0a800; }}
        .panels {{ display: flex; gap: 20px; flex-wrap: wrap; max-width: 1200px; margin-left: auto; margin-right: auto; }}
        .panel {{ background: #fff; padding: 20px 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); flex: 1; min-width: 300px; }}
        .panel h3 {{ margin-top: 0; color: #333; font-size: 18px; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
        .form-group {{ margin-bottom: 15px; text-align: left; }}
        .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #555; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛠️ GM 控制台</h1>
        <a href="/">返回游戏主页</a>
    </div>
    
    <div class="container">
        <h3>👥 1. 角色属性管理</h3>
        <table>
            <tr>
                <th style="width: 100px;">UID</th>
                <th>角色名</th>
                <th style="width: 130px;">金币</th>
                <th style="width: 130px;">金券</th>
                <th style="width: 90px;">等级</th>
                <th style="width: 90px;">操作</th>
                <th style="width: 200px;">危险操作</th>
            </tr>"""
        
        for u in users:
            uid = u['id'] + 100000
            html += f"""
            <tr>
                <form method="POST" action="/gm">
                    <input type="hidden" name="action" value="update_user">
                    <input type="hidden" name="uid" value="{uid}">
                    <td style="font-weight: bold; color: #007bff; font-size: 16px;">{uid}</td>
                    <td style="color: #666;">{u['username']}</td>
                    <td><input type="number" name="money" value="{u['money']}"></td>
                    <td><input type="number" name="rmb_money" value="{u['rmb_money']}"></td>
                    <td><input type="number" name="level" value="{u['level']}"></td>
                    <td><button type="submit" class="btn btn-success">保存</button></td>
                </form>
                <td>
                    <form method="POST" action="/gm" style="display:inline;">
                        <input type="hidden" name="action" value="clear_orgs">
                        <input type="hidden" name="uid" value="{uid}">
                        <button type="submit" class="btn btn-warning" onclick="return confirm('确定清空 UID: {uid} 的所有植物吗？');">清空植物</button>
                    </form>
                    <form method="POST" action="/gm" style="display:inline; margin-left: 5px;">
                        <input type="hidden" name="action" value="delete_user">
                        <input type="hidden" name="uid" value="{uid}">
                        <button type="submit" class="btn btn-danger" onclick="return confirm('⚠️ 警告：确定要彻底删除 UID: {uid} 的账号吗？\\n此操作不可逆，玩家的所有数据将灰飞烟灭！');">删除账号</button>
                    </form>
                </td>
            </tr>"""
        
        html += f"""
        </table>
    </div>
    
    <div class="panels">
        <div class="panel">
            <h3>📦 2. 物品发送</h3>
            <form method="POST" action="/gm">
                <input type="hidden" name="action" value="add_tool">
                <div class="form-group">
                    <label>玩家 UID:</label>
                    <select name="uid" required>
                        {options_html}
                    </select>
                </div>
                <div class="form-group">
                    <label>道具ID:</label>
                    <input type="number" name="tool_id" required>
                </div>
                <div class="form-group">
                    <label>数量:</label>
                    <input type="number" name="amount" value="99" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;">确认发送</button>
            </form>
        </div>
        
        <div class="panel">
            <h3>🌲 3. 世界之树</h3>
            <form method="POST" action="/gm">
                <input type="hidden" name="action" value="reset_tree">
                <div class="form-group">
                    <label>玩家 UID:</label>
                    <select name="uid" required>
                        {options_html}
                    </select>
                </div>
                <button type="submit" class="btn btn-warning" style="width:100%;">重置高度</button>
            </form>
        </div>

        <div class="panel">
            <h3>👯 4. 账号数据克隆</h3>
            <form method="POST" action="/gm">
                <input type="hidden" name="action" value="clone_user">
                <div class="form-group">
                    <label>数据来源 (被复制的大号):</label>
                    <select name="source_uid" required>
                        {options_html}
                    </select>
                </div>
                <div class="form-group">
                    <label>覆盖目标 (接收数据的新号):</label>
                    <select name="target_uid" required>
                        {options_html}
                    </select>
                </div>
                <button type="submit" class="btn btn-danger" style="width:100%;" onclick="return confirm('⚠️ 严重警告：目标账号现有的金钱、物品和植物将被彻底清空并被源账号覆盖！\\n\\n确认执行克隆吗？');">🚀 确认执行克隆覆盖</button>
            </form>
        </div>
    </div>
</body>
</html>"""
        return html

    @staticmethod
    def handle_post(form):
        """处理 GM 网页端的表单提交"""
        action = form.get('action')
        
        # 【新增】拦截账号克隆逻辑
        if action == 'clone_user':
            from dal import get_username_by_uid
            try:
                src_uid = int(form.get('source_uid', 0))
                tgt_uid = int(form.get('target_uid', 0))
            except ValueError: return
                
            src_user = get_username_by_uid(src_uid)
            tgt_user = get_username_by_uid(tgt_uid)
            # 确保不能自己克隆给自己
            if src_user and tgt_user and src_user != tgt_user:
                clone_user_data(src_user, tgt_user)
            return

        # 常规单号操作拦截
        uid_str = form.get('uid')
        if not uid_str: return
        
        from dal import get_username_by_uid
        try: uid = int(uid_str)
        except ValueError: return
            
        username = get_username_by_uid(uid)
        if not username: return
        
        if action == 'update_user': update_user_gm(username, form['money'], form['rmb_money'], form['level'])
        elif action == 'add_tool': modify_tool_amount(username, int(form['tool_id']), int(form['amount']))
        elif action == 'clear_orgs': clear_organisms(username)
        elif action == 'reset_tree': reset_tree_gm(username)
        elif action == 'delete_user': delete_user(username)

    