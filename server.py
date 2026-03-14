import socket
import selectors
import json

# Create a selector to monitor multiple sockets for I/O events
sel = selectors.DefaultSelector()
# List of all connected client sockets
clients = []

HOST = "localhost"
PORT = 65432


def accept_connection(server_socket):
    # Pull a completed connection off the kernel's backlog
    client_socket, addr = server_socket.accept()
    # Set non-blocking so recv() returns immediately if no data is available
    client_socket.setblocking(False)
    # Register the new client socket with the selector, using read_client as its callback
    sel.register(client_socket, selectors.EVENT_READ, read_client)
    clients.append(client_socket)
    print(f"Client connected at {addr[0]}:{addr[1]}")


def read_client(client_socket):
    try:
        # Read up to 4096 bytes from the client
        data = client_socket.recv(4096)

        # If the socket received no data then we know a client disconnected
        if not data:
            return disconnect(client_socket)
        
        # decode data
        payload = data.decode()

        # convert json string to dict
        payload = json.loads(payload)

        if payload["type"] == "chat_message":
            client_host, client_port = client_socket.getpeername()
            message = payload["message"]
            outbound_message = f"[{client_host}:{client_port}] {message}"

            # Log the message to a file
            with open("messages.txt", "a") as f:
                f.write(outbound_message + "\n")

            # Send the message to all other connected clients
            outbound_data = outbound_message.encode()
            broadcast(outbound_data, client_socket)
        elif payload["type"] == "chat_history_request":
            pass
        else:
            print("else statement")
            # Empty data means the client disconnected
            disconnect(client_socket)
    except ConnectionResetError:
        print("here")
        disconnect(client_socket)


def broadcast(message, sender_socket):
    # Send the message to every client except the sender
    for client in clients:
        if client is not sender_socket:
            try:
                client.sendall(message)
            except BrokenPipeError:
                disconnect(client)


def disconnect(client_socket):
    # Remove the socket from the selector and clients list, then close it
    sel.unregister(client_socket)
    clients.remove(client_socket)
    client_socket.close()
    print("A client has disconnected.")


def main():
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse of the address so we can restart the server quickly
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    # Tell the kernel to start accepting connections and queue them in a backlog
    server_socket.listen()
    # Set non-blocking so accept() doesn't block the event loop
    server_socket.setblocking(False)
    # Register the listening socket; accept_connection is stored as key.data
    sel.register(server_socket, selectors.EVENT_READ, accept_connection)

    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            # Block until at least one registered socket has an event
            events = sel.select()
            for key, _ in events:
                # key.data holds the callback: accept_connection or read_client
                callback = key.data
                # key.fileobj is the socket that triggered the event
                callback(key.fileobj)
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        # Clean up all client connections
        for client in clients:
            client.close()
        server_socket.close()
        sel.close()


if __name__ == "__main__":
    main()
