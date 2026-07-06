# Tor-Routed Comms TLS

A terminal-based secure chat application built in Python.

This project provides a client-server chat system that uses TLS for encrypted transport and supports Tor-routed `.onion` connections from the client side.

## What it is

`Tor-Routed Comms TLS` is a simple secure messaging proof-of-concept. It includes:
- a TLS-enabled chat server (`server/`)
- a terminal chat client (`client/`)
- certificate generation and setup helpers
- Tor SOCKS5 support for `.onion` clients
- colorful terminal UI with streaming text for messages

## Why it exists

The project is designed to demonstrate secure terminal communication over an encrypted channel and to support privacy-preserving routing through the Tor network. It is useful for learning about:
- TLS setup in Python
- self-signed certificate generation and pinning
- socket-based client/server chat architecture
- client-side Tor routing via SOCKS5
- terminal UI styling with `rich` and `colorama`

## Features

- TLS-secured chat transport using `ssl`
- Self-signed certificate generation for server and client
- Server broadcast chat architecture
- Client-side Tor support for `.onion` hosts
- Environment-configurable host and port
- Simple `start_server.py` and `start_client.py` launchers
- TLS connection test script

## Prerequisites

- Python 3.8+ (recommended)
- `pip` package manager
- Optional: Tor installed and running locally for `.onion` support

## Installation

1. Clone or copy the repository.
2. Change into the project directory:

```powershell
cd c:\Users\benne\TECH\Projects\Tor-Routed-Comms-TLS
```

3. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Run setup to create the default `.env` file and generate TLS certificates:

```powershell
python setup.py
```

This will create:
- `.env` with `SERVER_IP=127.0.0.1` and `PORT=4444`
- `server/key.pem`
- `server/cert.pem`
- `client/cert.pem`

## Configuration

The project uses `.env` configuration values:

- `SERVER_IP` — server bind address, typically `127.0.0.1`
- `PORT` — port for server and client

If you want to experiment with Tor, set `SERVER_IP` to your `.onion` address in the client environment, and ensure Tor is running locally.

## Running the server

Start the server with:

```powershell
python start_server.py
```

The server binds to the configured address and port and accepts TLS client connections.

## Running the client

Start the client with:

```powershell
python start_client.py
```

The client reads the configured server host and port from `.env` and connects using TLS.

### Using Tor

To connect through Tor to an `.onion` address:

1. Start Tor locally so the SOCKS5 proxy is available at `127.0.0.1:9050`.
2. Set `SERVER_IP` in `.env` to your `.onion` host.
3. Start the client normally.

The client code will detect a `.onion` host and route the connection through Tor.

> Note: The server itself does not launch Tor. If you want a hidden service, you must run Tor separately and configure the hidden service to forward to the server's local port.

## Testing

A simple TLS verification script is included:

```powershell
python test_tls.py
```

This script will:
- verify certificates exist
- start the server briefly
- start the client and verify the TLS handshake

## Project layout

- `start_server.py` — root launcher for the server
- `start_client.py` — root launcher for the client
- `generate_cert.py` — creates `server/key.pem`, `server/cert.pem`, and copies `client/cert.pem`
- `setup.py` — helper to initialize `.env` and generate certificates
- `test_tls.py` — TLS connectivity verification
- `server/` — server implementation and TLS-enabled socket handling
- `client/` — client implementation and Tor/TLS socket handling
- `requirements.txt` — Python dependencies

## Notes

- This project uses self-signed certificates. The client pins the server certificate from `client/cert.pem`.
- The chat protocol is newline-delimited JSON messages over an SSL socket.
- For production use, upgrade to a valid CA certificate and add authentication/user identity handling.

## Acknowledgements

Built with Python, `dotenv`, `colorama`, `rich`, `PySocks`, and `cryptography`.
