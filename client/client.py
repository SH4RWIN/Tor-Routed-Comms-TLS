"""
Dark Comm Chat Client
Main client application using the socket handler module
"""

import os
import time
import threading
import random
from dotenv import load_dotenv
from colorama import init, Fore, Style
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt
from rich.align import Align
from socket_handler import ClientSocketHandler

# Initialize colorama for Windows compatibility
init(autoreset=True)

# Initialize Rich console
console = Console()

# Load environment variables
load_dotenv()

# Change this line in the client.py file
server_ip = os.getenv("SERVER_IP", "localhost")  # Use hostname instead of IP
port = int(os.getenv("PORT"))

class ChatClient:
    def __init__(self):
        self.socket_handler = ClientSocketHandler(server_ip, port)
        self.username = None
        self.user_colors = {}
        self.available_colors = [
            Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, 
            Fore.MAGENTA, Fore.CYAN, Fore.WHITE, Fore.LIGHTRED_EX,
            Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX,
            Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX
        ]
        self.message_history = []
        self.running = True
        self.display_lock = threading.Lock()
        
    def get_user_color(self, username):
        """Get or assign a color for a username"""
        if username not in self.user_colors:
            # Assign a random color from available colors
            used_colors = set(self.user_colors.values())
            available = [c for c in self.available_colors if c not in used_colors]
            if not available:
                # If all colors used, pick randomly
                available = self.available_colors
            self.user_colors[username] = random.choice(available)
        return self.user_colors[username]
    
    def stream_text(self, text, username, color):
        """Stream text character by character, completing in exactly 2 seconds"""
        if not text:
            return
            
        # Calculate delay per character to complete in 2 seconds
        total_chars = len(text)
        if total_chars == 0:
            return
            
        delay_per_char = 2.0 / total_chars
        
        # Print username with color
        print(f"{color}[{username}]{Style.RESET_ALL}: ", end="", flush=True)
        
        # Stream each character
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay_per_char)
        
        # Move to next line
        print()
    
    def display_welcome(self):
        """Display welcome screen"""
        console.clear()
        
        welcome_text = Text("🌐 Onion Routed Chat Client", style="bold blue")
        subtitle = Text("A terminal based secure chat application", style="italic dim")
        
        welcome_panel = Panel(
            Align.center(welcome_text + "\n\n" + subtitle),
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(welcome_panel)
        console.print()
    
    def get_username(self):
        """Get username from user with beautiful prompt"""
        while True:
            username = Prompt.ask(
                "[bold cyan]Enter your username[/bold cyan]",
                default="Anonymous"
            ).strip()
            
            if username and len(username) <= 20:
                self.username = username
                break
            else:
                console.print("[red]Username must be 1-20 characters long[/red]")
        
        # Assign color to this user
        self.get_user_color(username)
    
    def display_chat_header(self):
        """Display chat header with connection info"""
        header_text = f"Connected to {server_ip}:{port} | User: {self.username} | Type 'exit' to quit"
        console.print(f"[dim]{header_text}[/dim]")
        console.print("─" * len(header_text))
        console.print()
    
    def display_message(self, message_data):
        """Display a received message with streaming effect"""
        username = message_data.get('username', 'Unknown')
        text = message_data.get('text', '')
        
        # Get color for this user
        color = self.get_user_color(username)
        
        # Add to message history
        self.message_history.append({
            'username': username,
            'text': text,
            'timestamp': time.time()
        })
        
        with self.display_lock:
            # Clear the current line and move to next line
            print("\r" + " " * 100 + "\r", end="", flush=True)
            print()  # Move to next line
            
            # Stream the message on a new line
            self.stream_text(text, username, color)
            
            # Ensure we're on a new line after the message
            print()
            
            # Redraw the prompt
            print(self.get_input_prompt(), end="", flush=True)
    
    def handle_error(self, error_message):
        """Handle connection errors"""
        console.print(f"[red]Error: {error_message}[/red]")
        self.running = False
    
    def get_input_prompt(self):
        """Get a beautiful input prompt"""
        color = self.get_user_color(self.username)
        return f"{color}[{self.username}]{Style.RESET_ALL} > "
    
    def send_message(self, text):
        """Send a message to the server"""
        if not text.strip():
            return
            
        message_data = {
            'username': self.username,
            'text': text.strip()
        }
        
        return self.socket_handler.send_message(message_data)
    
    def run(self):
        """Main chat loop"""
        try:
            # Display welcome screen
            self.display_welcome()
            
            # Get username
            self.get_username()
            
            # Set up socket handler callbacks
            self.socket_handler.set_message_callback(self.display_message)
            self.socket_handler.set_error_callback(self.handle_error)
            
            # Connect to server
            if not self.socket_handler.run_client():
                console.print("[red]Failed to connect to server[/red]")
                return
            
            # Display chat header
            self.display_chat_header()
            
            # Send join message
            self.send_message(f"{self.username} joined the chat!")
            
            # Display initial prompt
            print(self.get_input_prompt(), end="", flush=True)
            
            # Main input loop
            while self.running and self.socket_handler.is_connected():
                try:
                    # Get user input with beautiful prompt
                    user_input = input()
                    
                    if user_input.lower() == 'exit':
                        self.running = False
                        self.send_message(f"{self.username} left the chat!")
                        break
                    elif user_input.strip():
                        self.send_message(user_input)
                        # Redraw prompt after sending message
                        print(self.get_input_prompt(), end="", flush=True)
                        
                except KeyboardInterrupt:
                    self.running = False
                    self.send_message(f"{self.username} left the chat!")
                    break
                except EOFError:
                    self.running = False
                    break
                    
        except Exception as e:
            console.print(f"[red]Connection error: {e}[/red]")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.socket_handler.cleanup()
        console.print("\n[yellow]Disconnected from chat server.[/yellow]")

def main():
    client = ChatClient()
    client.run()

if __name__ == "__main__":
    main()