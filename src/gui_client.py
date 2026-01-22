import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from constants import MESSAGE_SIZE_IN_BYTES

CLR_SIDEBAR = "#1E293B"
CLR_BG = "#F8FAFC"
CLR_PRIMARY = "#4F46E5"
CLR_TEXT_DARK = "#0F172A"
CLR_SYSTEM = "#94A3B8"
CLR_NOTIFY = "#EF4444" 

class ChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Messenger")
        self.master.geometry("1000x700")
        
        self.name = ""
        self.client_socket = None
        self.current_chat_target = "Group Chat"
        self.chat_histories = {"Group Chat": []}
        self.unread_counts = {}

        self.paned_window = tk.PanedWindow(master, orient=tk.HORIZONTAL, bg="#E2E8F0", sashwidth=4, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(self.paned_window, bg=CLR_SIDEBAR, width=250)
        tk.Label(self.sidebar, text="CHANNELS", font=("Segoe UI", 10, "bold"), bg=CLR_SIDEBAR, fg="#64748B").pack(pady=(30, 10), padx=20, anchor="w")
        
        self.user_listbox = tk.Listbox(self.sidebar, bd=0, font=("Segoe UI", 11), bg=CLR_SIDEBAR, fg="#F1F5F9", selectbackground="#334155", highlightthickness=0, activestyle='none', cursor="hand2")
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=10)
        self.user_listbox.bind("<<ListboxSelect>>", self.on_user_select)

        self.main_frame = tk.Frame(self.paned_window, bg=CLR_BG)
        self.paned_window.add(self.sidebar, minsize=150)
        self.paned_window.add(self.main_frame, minsize=400)

        self.header = tk.Frame(self.main_frame, bg="white", height=70)
        self.header.pack(fill=tk.X)
        self.chat_title_label = tk.Label(self.header, text="Group Chat", font=("Segoe UI", 14, "bold"), bg="white", fg=CLR_TEXT_DARK)
        self.chat_title_label.pack(side=tk.LEFT, padx=25, pady=20)
        self.self_info = tk.Label(self.header, text="", font=("Segoe UI", 10), bg="white", fg=CLR_SYSTEM)
        self.self_info.pack(side=tk.RIGHT, padx=25)

        self.chat_area = scrolledtext.ScrolledText(self.main_frame, state='disabled', font=("Segoe UI", 11), bg="white", relief=tk.FLAT, padx=20, pady=20)
        self.chat_area.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)
        
        self.chat_area.tag_config("me", justify='right', foreground=CLR_PRIMARY, font=("Segoe UI", 11, "bold"))
        self.chat_area.tag_config("other", justify='left', foreground=CLR_TEXT_DARK)
        self.chat_area.tag_config("system", justify='center', foreground=CLR_SYSTEM, font=("Segoe UI", 9, "italic"))
        self.chat_area.tag_config("private", justify='left', foreground="#7C3AED", font=("Segoe UI", 11, "bold"))

        self.entry_frame = tk.Frame(self.main_frame, bg=CLR_BG)
        self.entry_frame.pack(fill=tk.X, padx=25, pady=20)
        self.msg_entry = tk.Entry(self.entry_frame, font=("Segoe UI", 12), relief=tk.FLAT, bd=8)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        self.send_btn = tk.Button(self.entry_frame, text="Send", font=("Segoe UI", 11, "bold"), bg=CLR_PRIMARY, fg="white", relief=tk.FLAT, command=self.send_message, padx=25)
        self.send_btn.pack(side=tk.RIGHT)

        self.master.after(100, self.ask_name)

    def ask_name(self):
        name = simpledialog.askstring("Welcome", "Please enter your name:")
        if name:
            self.name = name.strip()
            self.self_info.config(text=f"Logged in as: {self.name}")
            self.connect_to_server()
        else: 
            self.master.destroy()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', 12345))
            id_data = self.client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode().split("\n")[0]
            self.client_socket.sendall(f"{id_data}:{self.name}".encode())
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as _:
            messagebox.showerror("Error", "Could not connect.")
            self.master.destroy()

    def receive_messages(self):
        buffer = ""
        while True:
            try:
                data = self.client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode()
                if not data: 
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line: self.process_line(line)
            except Exception as _: 
                break

    def process_line(self, data):
        if data.startswith("USER_LIST:"):
            users = data.split(":")[1].split(",")
            self.update_sidebar(users)

        elif data.startswith("PRIVATE from "):
            header, content = data.split(": ", 1)
            sender = header.replace("PRIVATE from ", "")
            self.save_and_display(sender, f"{sender}: {content}", "private")

            if sender != self.current_chat_target:
                self.unread_counts[sender] = self.unread_counts.get(sender, 0) + 1
                self.update_sidebar_display()
        
        elif data.startswith("SYSTEM:"):
            self.save_and_display("Group Chat", data, "system")
            if self.current_chat_target != "Group Chat":
                self.unread_counts["Group Chat"] = self.unread_counts.get("Group Chat", 0) + 1
                self.update_sidebar_display()
        
        else:
            self.save_and_display("Group Chat", data, "other")
            if self.current_chat_target != "Group Chat":
                self.unread_counts["Group Chat"] = self.unread_counts.get("Group Chat", 0) + 1
                self.update_sidebar_display()

    def update_sidebar(self, users):
        current_users = ["Group Chat"] + [u.strip() for u in users if u.strip() and u.strip() != self.name]
        for user in current_users:
            if user not in self.chat_histories:
                self.chat_histories[user] = []
        
        self.update_sidebar_display(current_users)

    def update_sidebar_display(self, user_list=None):
        if user_list is None:
            user_list = []
            for i in range(self.user_listbox.size()):
                raw_text = self.user_listbox.get(i)
                user_name = raw_text.split(" (")[0]
                user_list.append(user_name)

        self.user_listbox.delete(0, tk.END)
        for user in user_list:
            display_text = user
            count = self.unread_counts.get(user, 0)
            if count > 0:
                display_text += f" ({count})"
            
            self.user_listbox.insert(tk.END, display_text)
            if count > 0:
                self.user_listbox.itemconfig(tk.END, fg=CLR_NOTIFY)

    def on_user_select(self, event):
        selection = self.user_listbox.curselection()
        if selection:
            raw_target = self.user_listbox.get(selection[0])
            new_target = raw_target.split(" (")[0]
            
            if new_target != self.current_chat_target:
                self.current_chat_target = new_target
                self.unread_counts[new_target] = 0
                self.chat_title_label.config(text=new_target)
                self.update_sidebar_display()
                self.refresh_display()

    def refresh_display(self):
        self.chat_area.config(state='normal')
        self.chat_area.delete('1.0', tk.END)
        for text, tag in self.chat_histories.get(self.current_chat_target, []):
            self.chat_area.insert(tk.END, text + "\n", tag)
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

    def save_and_display(self, chat_id, text, tag):
        if chat_id not in self.chat_histories: self.chat_histories[chat_id] = []
        self.chat_histories[chat_id].append((text, tag))
        
        if self.current_chat_target == chat_id:
            self.chat_area.config(state='normal')
            self.chat_area.insert(tk.END, text + "\n", tag)
            self.chat_area.config(state='disabled')
            self.chat_area.see(tk.END)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg: return
        if self.current_chat_target == "Group Chat":
            self.client_socket.sendall(msg.encode())
            self.save_and_display("Group Chat", f"You: {msg}", "me")
        else:
            self.client_socket.sendall(f"/msg {self.current_chat_target}: {msg}".encode())
            self.save_and_display(self.current_chat_target, f"You: {msg}", "me")
        self.msg_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()