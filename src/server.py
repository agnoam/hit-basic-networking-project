import socket
import threading
import argparse
import signal
import sys
from constants import MESSAGE_SIZE_IN_BYTES

clients = []
client_counter = 0
running = True

def broadcast_user_list():
    names = [c[2] for c in clients]
    user_list_msg = f"USER_LIST:{','.join(names)}\n"
    for sock, _, _ in clients:
        try:
            sock.sendall(user_list_msg.encode())
        except Exception as _: 
            pass

def broadcast(message, sender_socket=None):
    formatted_msg = f"{message}\n"
    for client_socket, _, _ in clients:
        if client_socket != sender_socket:
            try:
                client_socket.sendall(formatted_msg.encode())
            except Exception as _: 
                continue

def shutdown_server():
    global running
    if not running: 
        return
    
    print("Shutting down server...")
    broadcast("SYSTEM: SERVER_SHUTTING_DOWN")
    running = False
    for sock, _, _ in clients:
        try: 
            sock.close()
        except Exception as _: 
            pass

    clients.clear()

def signal_handler(signum, frame):
    shutdown_server()
    sys.exit(0)

def listen_for_exit():
    while running:
        try:
            if input().strip().upper() == "EXIT":
                shutdown_server()
                break
        except EOFError: 
            break

def handle_single_client(client_socket, client_address):
    global client_counter
    try:
        client_id = client_counter
        client_counter += 1
        client_socket.sendall(f"{client_id}\n".encode())
        
        data = client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode().strip()
        id_str, name = data.split(':', 1)
        
        clients.append((client_socket, id_str, name))
        broadcast_user_list()
        broadcast(f"SYSTEM: {name} joined.")

        while running:
            data = client_socket.recv(MESSAGE_SIZE_IN_BYTES)
            if not data: 
                break
            
            message = data.decode().strip()
            if message.startswith("/msg "):
                parts = message.split(" ", 2)
                if len(parts) >= 3:
                    target, content = parts[1], parts[2]
                    for sock, _, n in clients:
                        if n == target:
                            sock.sendall(f"PRIVATE from {name}: {content}\n".encode())
                            break
            else:
                broadcast(f"{name}: {message}", client_socket)
    except Exception as _: 
        pass
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
    server.settimeout(1.0)
    
    signal.signal(signal.SIGINT, signal_handler)
    threading.Thread(target=listen_for_exit, daemon=True).start()

    print(f"Server on port {args.port}. Type 'EXIT' to stop.")
    while running:
        try:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_single_client, 
                args=(conn, addr),
                daemon=True
            ).start()
        except socket.timeout: 
            continue
    
    server.close()

if __name__ == "__main__":
    main()