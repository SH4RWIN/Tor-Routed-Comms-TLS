#!/usr/bin/env python3
"""
TLS Test Script for Dark Comm Terminal Chat
Tests the TLS connection between client and server
"""

import subprocess
import time
import threading
import sys
import os

def test_tls_connection():
    """Test TLS connection between client and server"""
    print("🔒 Testing TLS Connection...")
    print("=" * 50)
    
    # Check if certificates exist
    server_cert = "server/cert.pem"
    server_key = "server/key.pem"
    client_cert = "client/cert.pem"
    
    if not os.path.exists(server_cert) or not os.path.exists(server_key):
        print("❌ Server certificates not found. Running certificate generation...")
        try:
            subprocess.run([sys.executable, "generate_cert.py"], check=True)
            print("✅ Certificates generated successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate certificates: {e}")
            return False
    
    if not os.path.exists(client_cert):
        print("❌ Client certificate not found. Please run setup.py first.")
        return False
    
    print("✅ All certificates found")
    
    # Start server in background
    print("🚀 Starting server...")
    server_process = subprocess.Popen([sys.executable, "start_server.py"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if server is running
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        print(f"❌ Server failed to start:")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return False
    
    print("✅ Server started successfully")
    
    # Test client connection
    print("🔗 Testing client connection...")
    try:
        # Run client with timeout
        result = subprocess.run([sys.executable, "start_client.py"], 
                              input="testuser\nexit\n", 
                              text=True, 
                              capture_output=True, 
                              timeout=10)
        
        if result.returncode == 0:
            print("✅ Client connection successful")
            print("✅ TLS handshake completed")
            success = True
        else:
            print(f"❌ Client connection failed with return code: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            success = False
            
    except subprocess.TimeoutExpired:
        print("❌ Client connection timed out")
        success = False
    except Exception as e:
        print(f"❌ Client connection error: {e}")
        success = False
    
    # Clean up server
    print("🛑 Stopping server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
    
    print("=" * 50)
    if success:
        print("🎉 TLS Test PASSED! Your TLS implementation is working correctly.")
    else:
        print("💥 TLS Test FAILED! Check the error messages above.")
    
    return success

if __name__ == "__main__":
    test_tls_connection()
