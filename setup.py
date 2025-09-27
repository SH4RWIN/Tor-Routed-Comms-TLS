#!/usr/bin/env python3
"""
Setup script for Dark Comm Terminal Chat
"""

import os

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("SERVER_IP=127.0.0.1\n")
            f.write("PORT=4444\n")
        print("Created .env file with default settings")
    else:
        print(".env file already exists")

def generate_certificates():
    """Generate SSL certificates if they don't exist"""
    server_cert = "server/cert.pem"
    server_key = "server/key.pem"
    client_cert = "client/cert.pem"
    
    if not os.path.exists(server_cert) or not os.path.exists(server_key) or not os.path.exists(client_cert):
        print("Generating SSL certificates...")
        try:
            from generate_cert import generate_certificates
            generate_certificates()
        except ImportError:
            print("Warning: Could not import certificate generation. Please run 'python generate_cert.py' manually.")
    else:
        print("SSL certificates already exist")

def main():
    print("Setting up Dark Comm Terminal Chat...")
    create_env_file()
    generate_certificates()
    print("Setup complete!")
    print("\nTo start the server: python start_server.py")
    print("To start a client: python start_client.py")

if __name__ == "__main__":
    main()
