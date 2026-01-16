import socket
import threading
import argparse

# List to hold client sockets and their names
clients = []

def broadcast(message, sender_socket=None):
    """Broadcast a message to all clients except the sender."""
    for client_socket, _ in clients:
        if client_socket != sender_socket:
            try:
                client_socket.sendall(message.encode())
            except:
                # If sending fails, the client might have disconnected
                remove_client(client_socket)

def remove_client(client_socket):
    """Remove a client from the list and close the socket."""
    for i, (sock, name) in enumerate(clients):
        if sock == client_socket:
            clients.pop(i)
            broadcast(f"{name} left the chat.")
            print(f"{name} disconnected.")
            sock.close()
            break

def handle_client(client_socket, client_address):
    """Handle communication with a single client."""
    try:
        # Receive the client's name
        name = client_socket.recv(1024).decode().strip()
        if not name:
            name = f"Anonymous_{client_address[1]}"
        clients.append((client_socket, name))
        print(f"{name} connected from {client_address}")
        broadcast(f"{name} joined the chat.")
        
        while True:
            # Receive message from client
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode().strip()
            if message:
                full_message = f"{name}: {message}"
                print(full_message)
                broadcast(full_message, client_socket)
    except:
        pass
    finally:
        remove_client(client_socket)

def main():
    parser = argparse.ArgumentParser(description='Chat Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=12345, help='Port to listen on')
    args = parser.parse_args()
    
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Bind the socket to the host and port
        server_socket.bind((args.host, args.port))
        
        # Listen for incoming connections
        server_socket.listen(5)
        print(f"Chat server listening on {args.host}:{args.port}")
        
        while True:
            # Accept a connection
            client_socket, client_address = server_socket.accept()
            
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("=======================")
        print("Shutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
