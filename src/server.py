import socket
import threading
import argparse
import signal
import sys
from constants import MESSAGE_SIZE_IN_BYTES

clients = [] # רשימה של (socket, id, name)
client_counter = 0
running = True

def broadcast_user_list():
    """שליחת רשימת שמות מעודכנת לכל המחוברים עם תו מפריד"""
    names = [c[2] for c in clients]
    user_list_msg = f"USER_LIST:{','.join(names)}\n"
    for sock, _, _ in clients:
        try:
            sock.sendall(user_list_msg.encode())
        except: pass

def broadcast(message, sender_socket=None):
    """שידור הודעה לכל הקבוצה עם תו מפריד"""
    formatted_msg = f"{message}\n"
    for client_socket, _, _ in clients:
        if client_socket != sender_socket:
            try:
                client_socket.sendall(formatted_msg.encode())
            except: continue

def shutdown_server():
    """כיבוי מסודר של השרת וכל החיבורים הפתוחים"""
    global running
    if not running: return
    print("\nShutting down server...")
    broadcast("SYSTEM: SERVER_SHUTTING_DOWN")
    running = False
    for sock, _, _ in clients:
        try: sock.close()
        except: pass
    clients.clear()

def signal_handler(signum, frame):
    """טיפול ב-Ctrl+C"""
    shutdown_server()
    sys.exit(0)

def listen_for_exit():
    """הקשבה לפקודת EXIT בטרמינל"""
    while running:
        try:
            if input().strip().upper() == "EXIT":
                shutdown_server()
                break
        except EOFError: break

def handle_client(client_socket, client_address):
    """ניהול תקשורת מול לקוח בודד"""
    global client_counter
    try:
        client_id = client_counter
        client_counter += 1
        client_socket.sendall(f"{client_id}\n".encode())
        
        # קבלת שם המשתמש בתהליך ה-Handshake
        data = client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode().strip()
        id_str, name = data.split(':', 1)
        
        clients.append((client_socket, id_str, name))
        broadcast_user_list()
        broadcast(f"SYSTEM: {name} joined.")

        while running:
            data = client_socket.recv(MESSAGE_SIZE_IN_BYTES)
            if not data: break
            
            message = data.decode().strip()
            if message.startswith("/msg "):
                # לוגיקת הודעה פרטית: /msg {name} {content}
                parts = message.split(" ", 2)
                if len(parts) >= 3:
                    target, content = parts[1], parts[2]
                    for sock, _, n in clients:
                        if n == target:
                            sock.sendall(f"PRIVATE from {name}: {content}\n".encode())
                            break
            else:
                broadcast(f"{name}: {message}", client_socket)
    except: pass
    finally:
        for i, (sock, id_s, n) in enumerate(clients):
            if sock == client_socket:
                clients.pop(i)
                broadcast_user_list()
                broadcast(f"SYSTEM: {n} left.")
                break
        client_socket.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=12345)
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', args.port))
    server.listen(5)
    server.settimeout(1.0) # מאפשר בדיקת דגל running
    
    signal.signal(signal.SIGINT, signal_handler)
    threading.Thread(target=listen_for_exit, daemon=True).start()

    print(f"Server on port {args.port}. Type 'EXIT' to stop.")
    while running:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except socket.timeout: continue
    server.close()

if __name__ == "__main__":
    main()