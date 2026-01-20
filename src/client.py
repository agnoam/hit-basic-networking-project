import socket
import threading
import argparse

from constants import MESSAGE_SIZE_IN_BYTES

def process_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('--host', default='localhost', help='Server host to connect to')
    parser.add_argument('--port', type=int, default=12345, help='Server port to connect to')
    return parser.parse_args()


def receive_messages(client_socket: socket.socket) -> None:
    """
    Receive and print messages from the server.
    """
    while True:
        try:
            data = client_socket.recv(MESSAGE_SIZE_IN_BYTES)
            if not data:
                break
            print(data.decode())
        except:
            break


def main() -> None:
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    args = process_args()
    
    # Connect to the server
    client_socket.connect((args.host, args.port))
    
    # Receive client ID
    id_data = client_socket.recv(MESSAGE_SIZE_IN_BYTES).decode().strip()
    print(f"Your client ID: {id_data}")
    
    # Send the client's name
    name = input("Enter your name: ")
    client_socket.sendall(f"{id_data}:{name}".encode())
    
    # Start a thread to receive messages (enabling real-time chatting)
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()
    
    try:
        while True:
            message = input()
            if message.lower() == 'quit':
                break
            client_socket.sendall(message.encode())
    except KeyboardInterrupt:
        print("================")
        print("Disconnecting...")

    finally:
        # Close the socket
        client_socket.close()

if __name__ == "__main__":
    main()
