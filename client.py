import sys
import socket
import selectors

# Create a selector to monitor both stdin and the server socket
sel = selectors.DefaultSelector()

HOST = "localhost"
PORT = 65432


def main():
    # Create a TCP socket and connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    # Set non-blocking so recv() doesn't block the event loop
    client_socket.setblocking(False)

    # Register stdin (keyboard input) and the server socket with the selector
    sel.register(sys.stdin, selectors.EVENT_READ)
    sel.register(client_socket, selectors.EVENT_READ)

    print(f"Connected to {HOST}:{PORT}. Start typing messages:")

    try:
        while True:
            # Wait for either user input or an incoming message from the server
            events = sel.select()
            for key, _ in events:
                if key.fileobj is sys.stdin:
                    # User typed something — read it and send to the server
                    message = sys.stdin.readline().strip()
                    if message:
                        client_socket.sendall(message.encode())
                else:
                    # Server sent something — read and display it
                    data = client_socket.recv(4096)
                    if data:
                        print(data.decode())
                    else:
                        # Empty data means the server closed the connection
                        print("Server closed the connection.")
                        return
    except KeyboardInterrupt:
        print("\nDisconnected.")
    finally:
        # Clean up the selector and socket
        sel.unregister(sys.stdin)
        sel.unregister(client_socket)
        client_socket.close()
        sel.close()


if __name__ == "__main__":
    main()
