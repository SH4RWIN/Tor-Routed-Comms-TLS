"""
Dark Comm Chat Server
Main server application using the socket handler module
"""

import os
from dotenv import load_dotenv
from socket_handler import ServerSocketHandler

# Load environment variables
load_dotenv()

server_ip = os.getenv("SERVER_IP", "127.0.0.1")  # For Tor hidden service, bind to localhost
port = int(os.getenv("PORT", 4444))

def display_server_info(socket_handler):
    """Display server startup information"""
    print(f"{'='*60}")
    print(f"Secure Communication Terminal")
    print(f"{'='*60}")
    print(f"Server IP: {server_ip}")
    print(f"Port: {port}")
    print(f"Status: Running")
    print(f"Connected Clients: {socket_handler.get_connected_clients_count()}")
    print(f"{'='*60}")
    print()

def main():
    """Main server function"""
    # For Tor hidden service, ensure server binds to localhost only
    # The .onion address is managed by Tor and not used directly in the server code
    socket_handler = ServerSocketHandler(server_ip, port)
    try:
        # Start the server
        if not socket_handler.start_server():
            print("Failed to start server")
            return
        # Display server info
        display_server_info(socket_handler)
        # Run the server loop
        socket_handler.run_server_loop()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        socket_handler.cleanup()
        print("Server stopped")

if __name__ == "__main__":
    main()

    