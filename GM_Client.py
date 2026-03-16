# GM_Client.py (运行在你自己的电脑上)
import tkinter as tk
from tkinter import messagebox, ttk
import requests

# ================= 配置区 =================
# 填入你服务器的公网 IP 和端口
SERVER_URL =  "http://127.0.0.1:8080/api/gm_software"
GM_PASSWORD = "niubi666"  # 必须和刚才在 server.py 里设置的一样
# ==========================================

def send_request(action, data):
    data['password'] = GM_PASSWORD
    data['action'] = action
    try:
        response = requests.post(SERVER_URL, data=data, timeout=5)
        if response.status_code == 200:
            messagebox.showinfo("操作成功", response.text)
        else:
            messagebox.showerror("操作失败", response.text)
    except Exception as e:
        messagebox.showerror("网络错误", f"无法连接到服务器:\n{e}")

def btn_send_tool():
    user = entry_user.get()
    tool_id = entry_tool_id.get()
    amount = entry_amount.get()
    if not user or not tool_id or not amount:
        messagebox.showwarning("警告", "账号、道具ID、数量都必须填写！")
        return
    send_request('send_tool', {'username': user, 'tool_id': tool_id, 'amount': amount})

def btn_add_money():
    user = entry_user.get()
    money = entry_money.get() or 0
    rmb = entry_rmb.get() or 0
    # 【新增】获取输入框里的新货币值
    honor = entry_honor.get() or 0
    merit = entry_merit.get() or 0
    ticket = entry_ticket.get() or 0
    
    if not user:
        messagebox.showwarning("警告", "账号必须填写！")
        return
    # 【升级】把数据一起发给服务器
    send_request('add_money', {'username': user, 'money': money, 'rmb': rmb, 'honor': honor, 'merit': merit, 'ticket': ticket})
def btn_clear_money():
    user = entry_user.get()
    if not user:
        messagebox.showwarning("警告", "账号必须填写！")
        return
    # 发送一个确认弹窗，防止误触
    if messagebox.askyesno("急救确认", f"确定要清空 {user} 的所有货币吗？\n这通常用于修复充值过多导致的坏档。"):
        send_request('clear_money', {'username': user})


# ================= UI 界面绘制 =================
root = tk.Tk()
root.title("PvZ 私服终极 GM 管理系统 v1.0")
root.geometry("450x350")
root.configure(padx=20, pady=20)

tk.Label(root, text="🌿 PvZ 专属 GM 工具", font=("Microsoft YaHei", 16, "bold"), fg="#2e7d32").pack(pady=(0, 20))

# 账号输入区
frame_user = tk.Frame(root)
frame_user.pack(fill="x", pady=5)
tk.Label(frame_user, text="玩家账号:", width=10).pack(side="left")
entry_user = tk.Entry(frame_user, font=("Arial", 12))
entry_user.pack(side="left", fill="x", expand=True)

# 道具发送区
frame_tool = tk.LabelFrame(root, text="📦 物品发送", padx=10, pady=10)
frame_tool.pack(fill="x", pady=10)
tk.Label(frame_tool, text="道具ID:").grid(row=0, column=0, pady=5)
entry_tool_id = tk.Entry(frame_tool, width=10)
entry_tool_id.grid(row=0, column=1, padx=5)
tk.Label(frame_tool, text="数量:").grid(row=0, column=2)
entry_amount = tk.Entry(frame_tool, width=10)
entry_amount.grid(row=0, column=3, padx=5)
entry_amount.insert(0, "1")
tk.Button(frame_tool, text="发送物品", bg="#4caf50", fg="white", command=btn_send_tool).grid(row=0, column=4, padx=10)

# 货币充值区
frame_money = tk.LabelFrame(root, text="💰 全货币充值", padx=10, pady=10)
frame_money.pack(fill="x", pady=5)

# 第一排：金币和金券
tk.Label(frame_money, text="加金币:").grid(row=0, column=0, pady=5)
entry_money = tk.Entry(frame_money, width=10)
entry_money.grid(row=0, column=1, padx=5)
entry_money.insert(0, "100000")

tk.Label(frame_money, text="加金券:").grid(row=0, column=2)
entry_rmb = tk.Entry(frame_money, width=10)
entry_rmb.grid(row=0, column=3, padx=5)
entry_rmb.insert(0, "5000")

# 第二排：荣誉和功勋
tk.Label(frame_money, text="加荣誉:").grid(row=1, column=0, pady=5)
entry_honor = tk.Entry(frame_money, width=10)
entry_honor.grid(row=1, column=1, padx=5)
entry_honor.insert(0, "50000")

tk.Label(frame_money, text="加功勋:").grid(row=1, column=2)
entry_merit = tk.Entry(frame_money, width=10)
entry_merit.grid(row=1, column=3, padx=5)
entry_merit.insert(0, "50000")

# 第三排：礼券和按钮
tk.Label(frame_money, text="加礼券:").grid(row=2, column=0, pady=5)
entry_ticket = tk.Entry(frame_money, width=10)
entry_ticket.grid(row=2, column=1, padx=5)
entry_ticket.insert(0, "1000")

# 【新增】红色的清零急救按钮
tk.Button(frame_money, text="🆘 清零修复", bg="#f44336", fg="white", command=btn_clear_money).grid(row=2, column=2, padx=5, pady=5)

tk.Button(frame_money, text="一键充值所有", bg="#2196f3", fg="white", command=btn_add_money).grid(row=2, column=3, padx=5, pady=5)

root.mainloop()