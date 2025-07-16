import tkinter as tk
from tkinter import messagebox
import threading
import requests
import re
import time
import pyperclip

# 邮箱验证码获取逻辑，参数：邮箱Label、验证码Label、线程控制
class MailWorker(threading.Thread):
    def __init__(self, email_var, code_var, stop_event):
        super().__init__()
        self.email_var = email_var
        self.code_var = code_var
        self.stop_event = stop_event
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://linshiyou.com/",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:135.0) Gecko/20000101 Firefox/135.0",
            "x-requested-with": "XMLHttpRequest"
        })

    def run(self):
        # 获取邮箱
        url01 = "https://linshiyou.com/user.php"
        params01 = {"user": "@youxiang.dev"}
        email = None
        while not self.stop_event.is_set():
            try:
                resp1 = self.session.get(url01, params=params01, timeout=10)
                match = re.search(r'[\w.-]+@youxiang\.dev', resp1.text)
                if match:
                    email = match.group(0)
                    self.email_var.set(email)
                    break
            except Exception:
                pass
            time.sleep(1)
        if self.stop_event.is_set():
            return
        # 保存邮箱
        url02 = "https://linshiyou.com/actions.php"
        params02 = {"action": "saveEMails"}
        try:
            self.session.get(url02, params=params02, timeout=10)
        except Exception:
            pass
        # 轮询验证码
        url03 = "https://linshiyou.com/mail.php"
        params03 = {"unseen": "1"}
        while not self.stop_event.is_set():
            try:
                resp3 = self.session.get(url03, params=params03, timeout=10)
                html = resp3.text
                match = re.search(r"Anakin 邮箱验证码：([0-9]{6})", html)
                if match:
                    code = match.group(1)
                    self.code_var.set(code)
                    break
            except Exception:
                pass
            time.sleep(2)

# 单个线路的UI和控制
class LineFrame(tk.Frame):
    def __init__(self, master, line_num):
        super().__init__(master, relief=tk.RIDGE, borderwidth=2, padx=10, pady=10)
        self.line_num = line_num
        self.email_var = tk.StringVar()
        self.code_var = tk.StringVar()
        self.worker = None
        self.stop_event = threading.Event()
        self.master = master
        # UI
        tk.Label(self, text=f"线路{line_num+1}", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3)
        tk.Label(self, text="邮箱:").grid(row=1, column=0, sticky='e')
        self.email_entry = tk.Entry(self, textvariable=self.email_var, width=30, state='readonly')
        self.email_entry.grid(row=1, column=1, columnspan=2, sticky='w')
        self.email_entry.bind('<Button-1>', self.copy_email)
        tk.Label(self, text="验证码:").grid(row=2, column=0, sticky='e')
        self.code_entry = tk.Entry(self, textvariable=self.code_var, width=10, state='readonly')
        self.code_entry.grid(row=2, column=1, sticky='w')
        self.code_entry.bind('<Button-1>', self.copy_code)
        # 按钮
        self.start_btn = tk.Button(self, text="开始", command=self.start)
        self.start_btn.grid(row=3, column=0, pady=5)
        self.clear_btn = tk.Button(self, text="清空", command=self.clear)
        self.clear_btn.grid(row=3, column=2, pady=5)

    def show_toast(self, msg):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        x = self.winfo_rootx() + 80
        y = self.winfo_rooty() + 40
        toast.geometry(f'+{x}+{y}')
        label = tk.Label(toast, text=msg, bg='#222', fg='white', font=("Arial", 10), padx=10, pady=5)
        label.pack()
        toast.after(1000, toast.destroy)  # 1秒后自动关闭

    def start(self):
        self.clear()  # 清空旧数据
        self.stop_event.clear()
        self.worker = MailWorker(self.email_var, self.code_var, self.stop_event)
        self.worker.daemon = True
        self.worker.start()

    def copy_email(self, event=None):
        email = self.email_var.get()
        if email:
            pyperclip.copy(email)
            self.show_toast("邮箱已复制！")
        else:
            self.show_toast("没有可复制的邮箱！")

    def copy_code(self, event=None):
        code = self.code_var.get()
        if code:
            pyperclip.copy(code)
            self.show_toast("验证码已复制！")
        else:
            self.show_toast("没有可复制的验证码！")

    def clear(self):
        self.stop_event.set()
        self.email_var.set("")
        self.code_var.set("")

# 主窗口
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("临时邮箱验证码多线程获取")
        self.geometry("600x400")
        self.resizable(False, False)
        self.frames = []
        for i in range(4):
            frame = LineFrame(self, i)
            frame.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            self.frames.append(frame)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
    