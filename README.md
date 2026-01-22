# Networking Chat Project

This repository contains a simple socket-based chat application implemented in Python. It includes a server that manages client connections and facilitates private messaging, and a GUI client built with Tkinter for an interactive chat experience.

## Features

- **Server**: Handles multiple client connections, user authentication with unique names, and private messaging between users.
- **Client**: Graphical user interface for logging in, viewing connected users, and sending/receiving private messages.
- **Private Messaging**: Users can select another user from the list and send private messages.

## Installation

1. **Clone the repository**:

2. **Ensure Python 3.x is installed** (Python 3.6 or higher recommended).

3. **Install dependencies** (if not already installed):
   - Tkinter is usually included with Python, but on some systems (e.g., Linux), you may need to install it:
     - Ubuntu/Debian: `sudo apt-get install python3-tk`
     - macOS: Tkinter is included with Python from python.org
     - Windows: Tkinter is included with Python from python.org

   No additional packages are required beyond the standard library.

## Usage

1. **Start the Server**:
   - Open a terminal and navigate to the project directory.
   - Run: `python src/server.py`
   - The server will start listening on `127.0.0.1:12345`.

2. **Run the Client**:
   - Open another terminal (or multiple for testing).
   - Run: `python src/gui_client.py`
   - Enter a unique name when prompted to log in.
   - The client will connect to the server and display the list of connected users.
   - Select a user from the sidebar to start a private chat, or use "Group Chat" (though private messaging is the primary feature).

3. **Chatting**:
   - Type messages in the input field and press Enter or click Send.
   - Messages are sent privately to the selected user.
   - Received messages appear in the chat area.

## Project Structure

- `src/server.py`: The socket server handling connections and messaging.
- `src/gui_client.py`: The Tkinter-based GUI client.
- `src/constants.py`: Contains constants like message buffer size.
- `captures/`: Directory for network capture files (e.g., Wireshark captures).
- `docs/`: Documentation files.

## Notes

- The server must be running before starting clients.
- User names must be unique; duplicates will be rejected.
- This is a basic implementation for educational purposes and may not handle all edge cases in production.