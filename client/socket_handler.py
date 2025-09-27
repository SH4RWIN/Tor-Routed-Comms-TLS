"""
Client Socket Handler Module
Handles all socket connections and message communication for the chat client
"""

import socket
import socks  # PySocks for Tor proxy support
import ssl
import threading
import json
import time
from colorama import init, Fore, Style
import logging

# Initialize colorama for Windows compatibility
init(autoreset=True)

class ClientSocketHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        self.message_callback = None
        self.error_callback = None
        self.lock = threading.Lock()
        
    def set_message_callback(self, callback):
        """Set callback function for received messages"""
        self.message_callback = callback
    
    def set_error_callback(self, callback):
        """Set callback function for errors"""
        self.error_callback = callback
    
    def log_message(self, message, level="INFO"):
        """Log messages with timestamp and color coding"""
        timestamp = time.strftime("%H:%M:%S")
        color = Fore.GREEN if level == "INFO" else Fore.RED if level == "ERROR" else Fore.YELLOW
        print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")
    
    def connect(self):
        """Connect to the server via Tor if .onion, else direct"""
        try:
            # Create SSL context with proper security settings
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # Configure SSL security options
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            
            # Handle certificate verification based on connection type
            if self.host and self.host.endswith('.onion'):
                # For .onion addresses, use certificate pinning but disable hostname verification
                # since .onion addresses don't work with standard hostname verification
                context.load_verify_locations('client/cert.pem')
                context.check_hostname = False
                context.verify_mode = ssl.CERT_REQUIRED
                self.log_message("Using certificate pinning for .onion address")
            else:
                # For regular addresses, use standard verification
                context.load_verify_locations('client/cert.pem')
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                self.log_message("Using standard certificate verification")

            plain_socket = None
            if self.host and self.host.endswith('.onion'):
                # Use Tor SOCKS5 proxy
                plain_socket = socks.socksocket()
                plain_socket.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
                self.log_message(f"Connecting to {self.host}:{self.port} via Tor SOCKS5 proxy")
            else:
                plain_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.log_message(f"Connecting to {self.host}:{self.port} directly")

            # Wrap the socket with SSL
            # For .onion addresses, use localhost as server_hostname since cert is for localhost
            server_hostname = 'localhost' if (self.host and self.host.endswith('.onion')) else self.host
            self.socket = context.wrap_socket(plain_socket, server_hostname=server_hostname)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            self.log_message(f"Securely connected to {self.host}:{self.port}")
            return True
        except ssl.SSLError as ssl_err:
            self.log_message(f"SSL Error: {ssl_err}", "ERROR")
            self.log_message(f"SSL Error details: {ssl_err.library}:{ssl_err.reason}", "ERROR")
            if self.error_callback:
                self.error_callback(f"SSL connection failed: {ssl_err}")
            return False
        except Exception as e:
            self.log_message(f"Failed to connect to server: {e}", "ERROR")
            self.log_message(f"Error type: {type(e).__name__}", "ERROR")
            if self.error_callback:
                self.error_callback(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.log_message("Disconnected from server")
    
    def send_message(self, message_data):
        """Send a message to the server"""
        if not self.connected or not self.socket:
            self.log_message("Not connected to server", "ERROR")
            return False
        
        try:
            message_json = json.dumps(message_data) + "\n"
            self.socket.send(message_json.encode())
            return True
        except Exception as e:
            self.log_message(f"Failed to send message: {e}", "ERROR")
            if self.error_callback:
                self.error_callback(f"Send failed: {e}")
            return False
    
    def receive_messages(self):
        """Handle incoming messages from server"""
        buffer = ""
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024)
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
                        if self.message_callback:
                            self.message_callback(message_data)
                    except json.JSONDecodeError:
                        self.log_message(f"Received invalid JSON: {line}", "ERROR")
                        continue
                        
            except Exception as e:
                if self.running:
                    self.log_message(f"Error receiving messages: {e}", "ERROR")
                    if self.error_callback:
                        self.error_callback(f"Receive error: {e}")
                break
        
        # Connection lost
        self.connected = False
        if self.error_callback:
            self.error_callback("Connection lost")
    
    def start_receiving(self):
        """Start the message receiving thread"""
        if not self.connected:
            self.log_message("Not connected to server", "ERROR")
            return False
        
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()
        return True
    
    def is_connected(self):
        """Check if client is connected to server"""
        return self.connected and self.socket is not None
    
    def get_connection_info(self):
        """Get connection information"""
        if self.connected:
            return f"{self.host}:{self.port}"
        return "Not connected"
    
    def cleanup(self):
        """Clean up resources"""
        self.disconnect()
    
    def run_client(self):
        """Run the client"""
        if self.connect():
            return self.start_receiving()
        return False
