"""
Server Socket Handler Module
Handles all socket connections and message broadcasting for the chat server
"""

import socket
import ssl
import threading
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows compatibility
init(autoreset=True)

class ServerSocketHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.ssl_context = None
        self.clients = []
        self.client_info = {}  # Store client info (address, username, etc.)
        self.client_threads = []  # Track client threads for graceful shutdown
        self.running = False
        self.lock = threading.Lock()
        
    def log_message(self, message, level="INFO"):
        """Log messages with timestamp and color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = Fore.GREEN if level == "INFO" else Fore.RED if level == "ERROR" else Fore.YELLOW
        print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")
    
    def setup_ssl_context(self):
        """Set up the SSL context for the server"""
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Configure SSL security options
            self.ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            self.ssl_context.options |= ssl.OP_NO_SSLv2
            self.ssl_context.options |= ssl.OP_NO_SSLv3
            self.ssl_context.options |= ssl.OP_NO_TLSv1
            self.ssl_context.options |= ssl.OP_NO_TLSv1_1
            self.ssl_context.options |= ssl.OP_SINGLE_DH_USE
            self.ssl_context.options |= ssl.OP_SINGLE_ECDH_USE
            
            # Load certificate and key
            certfile_path = 'server/cert.pem'
            keyfile_path = 'server/key.pem'
            self.ssl_context.load_cert_chain(certfile=certfile_path, keyfile=keyfile_path)
            
            # Set minimum TLS version
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            self.log_message("SSL context created successfully with security hardening")
            return True
        except Exception as e:
            self.log_message(f"Failed to create SSL context: {e}", "ERROR")
            return False
    
    def create_socket(self):
        """Create and configure the server socket"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.log_message("Server socket created successfully")
            return True
        except Exception as e:
            self.log_message(f"Failed to create server socket: {e}", "ERROR")
            return False
    
    def bind_socket(self):
        """Bind the socket to host and port"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.log_message(f"Server bound to {self.host}:{self.port}")
            return True
        except Exception as e:
            self.log_message(f"Failed to bind socket: {e}", "ERROR")
            return False
    
    def start_listening(self, max_connections=5):
        """Start listening for connections"""
        try:
            self.server_socket.listen(max_connections)
            self.log_message(f"Server listening for connections (max: {max_connections})")
            return True
        except Exception as e:
            self.log_message(f"Failed to start listening: {e}", "ERROR")
            return False
    
    def accept_connection(self):
        """Accept a new client connection"""
        try:
            client_socket, address = self.server_socket.accept()
            with self.lock:
                self.clients.append(client_socket)
                self.client_info[client_socket] = {'address': address, 'username': None}
            self.log_message(f"New connection from {address}")
            return client_socket, address
        except Exception as e:
            self.log_message(f"Error accepting connection: {e}", "ERROR")
            return None, None
    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        buffer = ""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                buffer += data.decode()
                
                # Process newline-delimited JSON messages
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    
                    try:
                        message_data = json.loads(line)
                        self.process_message(client_socket, message_data)
                    except json.JSONDecodeError:
                        self.log_message(f"Invalid JSON from {address}: {line}", "ERROR")
                        continue
                        
        except Exception as e:
            self.log_message(f"Error handling client {address}: {e}", "ERROR")
        finally:
            self.disconnect_client(client_socket)
    
    def process_message(self, client_socket, message_data):
        """Process incoming message from client"""
        username = message_data.get('username', 'Unknown')
        text = message_data.get('text', '')
        
        # Update client info with username
        if client_socket in self.client_info:
            self.client_info[client_socket]['username'] = username
        
        # Log the message
        self.log_message(f"Message from {username}: {text}")
        
        # Broadcast to all other clients
        self.broadcast(message_data, client_socket)
    
    def broadcast(self, message_data, sender_socket):
        """Broadcast message to all clients except sender"""
        message_json = json.dumps(message_data) + "\n"
        message_bytes = message_json.encode()
        
        # Send to all clients except sender
        disconnected_clients = []
        with self.lock:
            for client in self.clients[:]:
                if client != sender_socket:
                    try:
                        client.send(message_bytes)
                    except Exception:
                        # Client disconnected
                        disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.disconnect_client(client)
    
    def disconnect_client(self, client_socket):
        """Handle client disconnection"""
        with self.lock:
            if client_socket in self.clients:
                self.clients.remove(client_socket)

            if client_socket in self.client_info:
                username = self.client_info[client_socket].get('username', 'Unknown')
                address = self.client_info[client_socket]['address']
                self.log_message(f"Client {username} ({address}) disconnected")
                del self.client_info[client_socket]

        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            client_socket.close()
        except:
            pass

    def get_connected_clients_count(self):
        """Get the number of connected clients"""
        with self.lock:
            return len(self.clients)
    
    def get_client_info(self):
        """Get information about connected clients"""
        with self.lock:
            return self.client_info.copy()
    
    def start_server(self):
        """Start the server and begin accepting connections"""
        if not self.setup_ssl_context():
            return False

        if not self.create_socket():
            return False
        
        if not self.bind_socket():
            return False
        
        if not self.start_listening():
            return False
        
        self.running = True
        self.log_message("Server started successfully")
        return True
    
    def run_server_loop(self):
        """Main server loop - accepts connections and handles them"""
        if not self.running:
            self.log_message("Server not started. Call start_server() first.", "ERROR")
            return

        try:
            while self.running:
                try:
                    # Accept new connection
                    client_socket, address = self.server_socket.accept()
                    # Wrap the client socket with SSL
                    try:
                        ssl_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                        self.log_message(f"SSL handshake successful for {address}")
                    except ssl.SSLError as ssl_err:
                        self.log_message(f"SSL handshake failed for {address}: {ssl_err}", "ERROR")
                        self.log_message(f"SSL Error details: {ssl_err.library}:{ssl_err.reason}", "ERROR")
                        client_socket.close()
                        continue
                    except Exception as e:
                        self.log_message(f"Unexpected error during SSL handshake for {address}: {e}", "ERROR")
                        client_socket.close()
                        continue

                    if ssl_socket and address:
                        with self.lock:
                            self.clients.append(ssl_socket)
                            self.client_info[ssl_socket] = {'address': address, 'username': None}
                        # Handle client in separate thread
                        client_thread = threading.Thread(
                            target=self.handle_client,
                            args=(ssl_socket, address),
                            daemon=True
                        )
                        client_thread.start()
                        with self.lock:
                            self.client_threads.append(client_thread)

                except KeyboardInterrupt:
                    self.log_message("Keyboard interrupt received, shutting down...")
                    break
                except Exception as e:
                    self.log_message(f"Error in server loop: {e}", "ERROR")

        finally:
            self.stop_server()
    
    def stop_server(self):
        """Stop the server and close all connections"""
        self.running = False

        # Close all client connections
        with self.lock:
            for client in self.clients[:]:
                self.disconnect_client(client)

        # Wait for all client threads to finish
        with self.lock:
            for thread in self.client_threads:
                if thread.is_alive():
                    thread.join(timeout=2)

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        self.log_message("Server stopped")

    def cleanup(self):
        """Clean up all resources"""
        self.stop_server()
