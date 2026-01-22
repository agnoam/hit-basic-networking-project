import socket
import threading

import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

from constants import MESSAGE_SIZE_IN_BYTES

COLOR_BG = "#F3F4F6"
COLOR_SIDEBAR = "#111827"
COLOR_HEADER = "#FFFFFF"
COLOR_PRIMARY = "#2563EB"
COLOR_MY_MSG = "#1D4ED8"

class ChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Python Secure Messenger")
        self.master.geometry("900x650")
        
        self.name = ""
        self.client_socket = None
        self.current_chat_target = "Group Chat"        
        self.chat_histories = {"Group Chat": []}

        self.sidebar = tk.Frame(master, bg=COLOR_SIDEBAR, width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="MESSAGES", font=("Arial", 10, "bold"), 
                 bg=COLOR_SIDEBAR, fg="#9CA3AF").pack(pady=(20, 10), padx=20, anchor="w")
        
        self.user_listbox = tk.Listbox(self.sidebar, bd=0, font=("Arial", 11), 
                                      bg=COLOR_SIDEBAR, fg="#F3F4F6", 
                                      selectbackground="#374151", highlightthickness=0)
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=10)
        self.user_listbox.bind("<<ListboxSelect>>", self.on_user_select)

        self.main_frame = tk.Frame(master, bg=COLOR_BG)
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.header = tk.Frame(self.main_frame, bg=COLOR_HEADER, height=70)
        self.header.pack(fill=tk.X)
        
        self.chat_title_label = tk.Label(self.header, text="Group Chat", font=("Arial", 14, "bold"), 
                                        bg=COLOR_HEADER, fg="#111827")
        self.chat_title_label.pack(side=tk.LEFT, padx=25, pady=20)
        
        self.self_name_label = tk.Label(self.header, text="", font=("Arial", 10), 
                                      bg=COLOR_HEADER, fg="#6B7280")
        self.self_name_label.pack(side=tk.RIGHT, padx=25)

        self.chat_area = scrolledtext.ScrolledText(self.main_frame, state='disabled', 
                                                  font=("Arial", 11), bg="white", 
                                                  relief=tk.FLAT, padx=20, pady=20)
        self.chat_area.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)
        
        self.chat_area.tag_config("me", foreground=COLOR_MY_MSG, font=("Arial", 11, "bold"))
        self.chat_area.tag_config("system", foreground="#9CA3AF", font=("Arial", 10, "italic"))
        self.chat_area.tag_config("private", foreground="#9333EA", font=("Arial", 11, "bold"))

        self.entry_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.entry_frame.pack(fill=tk.X, padx=25, pady=20)
        
        self.msg_entry = tk.Entry(self.entry_frame, font=("Arial", 12), relief=tk.FLAT)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(self.entry_frame, text="Send", font=("Arial", 11, "bold"), 
                                 bg=COLOR_PRIMARY, fg="white", relief=tk.FLAT, 
                                 command=self.send_message, padx=25)
        self.send_btn.pack(side=tk.RIGHT)

        self.master.after(100, self.ask_name)

    def ask_name(self):
        name = simpledialog.askstring("Login", "Enter your name:")
        if name:
            self.name = name.strip()
            self.self_name_label.config(text=f"Logged in as: {self.name}")
            self.connect_to_server()
        else: self.master.destroy()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', 12345))
            # קבלת ID ושליחת פרטים
            id_data = self.client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode().split("\n")[0]
            self.client_socket.sendall(f"{id_data}:{self.name}".encode())
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except:
            messagebox.showerror("Error", "Server not found.")
            self.master.destroy()

    def receive_messages(self):
        buffer = ""
        while True:
            try:
                data = self.client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode()
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line: self.process_line(line)
            except: break

    def process_line(self, data):
        if data.startswith("USER_LIST:"):
            users = data.split(":")[1].split(",")
            self.update_sidebar(users)
        elif data.startswith("PRIVATE from "):
            header, content = data.split(": ", 1)
            sender = header.replace("PRIVATE from ", "")
            self.save_and_display(sender, f"{sender}: {content}", "private")
        elif data.startswith("SYSTEM:"):
            self.save_and_display("Group Chat", data, "system")
        else:
            self.save_and_display("Group Chat", data, None)

    def update_sidebar(self, users):
        self.user_listbox.delete(0, tk.END)
        self.user_listbox.insert(tk.END, "Group Chat")
        for u in users:
            clean = u.strip()
            # סינון עצמי מהרשימה
            if clean and clean != self.name:
                self.user_listbox.insert(tk.END, clean)
                if clean not in self.chat_histories:
                    self.chat_histories[clean] = []

    def on_user_select(self, event):
        selection = self.user_listbox.curselection()
        if selection:
            target = self.user_listbox.get(selection[0])
            if target != self.current_chat_target:
                self.current_chat_target = target
                self.chat_title_label.config(text=target)
                self.refresh_display()

    def refresh_display(self):
        self.chat_area.config(state='normal')
        self.chat_area.delete('1.0', tk.END)
        for text, tag in self.chat_histories.get(self.current_chat_target, []):
            self.chat_area.insert(tk.END, text + "\n", tag)
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

    def save_and_display(self, chat_id, text, tag):
        if chat_id not in self.chat_histories: 
            self.chat_histories[chat_id] = []
        
        self.chat_histories[chat_id].append((text, tag))
        if self.current_chat_target == chat_id:
            self.chat_area.config(state='normal')
            self.chat_area.insert(tk.END, text + "\n", tag)
            self.chat_area.config(state='disabled')
            self.chat_area.see(tk.END)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg: 
            return
        
        if self.current_chat_target == "Group Chat":
            self.client_socket.sendall(msg.encode())
            self.save_and_display("Group Chat", f"You: {msg}", "me")
        else:
            self.client_socket.sendall(f"/msg {self.current_chat_target} {msg}".encode())
            self.save_and_display(self.current_chat_target, f"You (Private): {msg}", "me")
        
        self.msg_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()