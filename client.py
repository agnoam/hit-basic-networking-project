import socket
import threading
import argparse

def receive_messages(client_socket):
    """Receive and print messages from the server."""
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(data.decode())
        except:
            break

def main():
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('--host', default='localhost', help='Server host to connect to')
    parser.add_argument('--port', type=int, default=12345, help='Server port to connect to')
    args = parser.parse_args()
    
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Define the host and port
    host = args.host
    port = args.port
    
    # Connect to the server
    client_socket.connect((host, port))
    
    # Send the client's name
    name = input("Enter your name: ")
    client_socket.sendall(name.encode())
    
    # Start a thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()
    
    try:
        # Send messages
        while True:
            message = input()
            if message.lower() == 'quit':
                break
            client_socket.sendall(message.encode())
    except KeyboardInterrupt:
        print("\nDisconnecting...")
    finally:
        # Close the socket
        client_socket.close()

if __name__ == "__main__":
    main()
