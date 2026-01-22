import socket
import threading
import argparse
import signal

from constants import MESSAGE_SIZE_IN_BYTES

# List to hold client sockets and their names
clients = []
# Counter for client IDs
client_counter = 0
# Flag to control the server loop
running = True

def broadcast(message, sender_socket=None):
    """
    Broadcast a message to all clients except the sender.
    """
    for client_socket, _, _ in clients:
        if client_socket != sender_socket:
            try:
                client_socket.sendall(message.encode())
            except Exception as _:
                # If sending fails, the client might have disconnected
                remove_client(client_socket)

def remove_client(client_socket):
    """
    Remove a client from the list and close the socket.
    """
    for i, (sock, id_str, name) in enumerate(clients):
        if sock == client_socket:
            clients.pop(i)
            broadcast(f"[{id_str}]: {name} - left the chat.")
            print(f"[{id_str}]: {name} - disconnected.")
            sock.close()
            break

def signal_handler(signum, frame):
    """
    Handle SIGINT (Ctrl+C) to shut down the server gracefully.
    """
    global running
    print("=======================")
    print("Shutting down server...")
    broadcast("SERVER_SHUTTING_DOWN")
    running = False

def handle_client(client_socket: socket.socket, client_address):
    """
    Handle communication with a single client.
    """
    global client_counter
    client_id = client_counter
    client_counter += 1
    client_socket.sendall(str(client_id).encode())
    
    try:
        # Receive the client's id:name
        data = client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode().strip()
        id_str, name = data.split(':', 1)
        if not name:
            name = f"Anonymous_{client_address[1]}"

        clients.append((client_socket, id_str, name))
        print(f"[{id_str}]: {name} connected from {client_address}")
        broadcast(f"[{id_str}]: {name} joined the chat.")
        
        while True:
            # Receive message from client
            data = client_socket.recv(MESSAGE_SIZE_IN_BYTES)
            if not data:
                break
            message = data.decode().strip()
            if message:
                full_message = f"[{id_str}]: {name} - {message}"
                print(full_message)
                broadcast(full_message, client_socket)
    except Exception as _:
        pass
    finally:
        remove_client(client_socket)

def main():
    parser = argparse.ArgumentParser(description='Chat Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=12345, help='Port to listen on')
    parser.add_argument('--clients', type=int, default=5, help='Parallel users the socket will listen to')
    args = parser.parse_args()
    
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to the host and port
    server_socket.bind((args.host, args.port))
    
    # Listen for incoming connections
    server_socket.listen(args.clients)
    print(f"Chat server listening on {args.host}:{args.port}")
    
    # Set a timeout on the socket to make accept() non-blocking periodically
    server_socket.settimeout(1.0)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    while running:
        try:
            # Accept a connection
            client_socket, client_address = server_socket.accept()
            
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
        except socket.timeout:
            # Timeout occurred, check if we should continue running
            continue
        except InterruptedError:
            # Socket operation may fail if interrupted
            break
    
    # Shutdown: close all client sockets
    for sock, _, _ in clients:
        try:
            sock.close()
        except:
            pass
    clients.clear()
    server_socket.close()

if __name__ == "__main__":
    main()
