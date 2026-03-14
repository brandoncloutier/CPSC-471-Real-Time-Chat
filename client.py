import sys
import socket
import selectors
import json

HOST = "localhost"
PORT = 65432


def parse_port_arg():
    if len(sys.argv) < 2:
        print("[ Error ]: no args supplied")
        sys.exit(1)
    if len(sys.argv) > 2:
        print("[ Error ]: expected exactly one argument: <server port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
    except ValueError:
        print("[ Error ]: server port must be an integer")
        sys.exit(1)

    if port < 1 or port > 65535:
        print("[ Error ]: server port must be between 1 and 65535")
        sys.exit(1)

    return port

def chat_loop(port):
    sel = selectors.DefaultSelector()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, port))
    except ConnectionRefusedError:
        print("[ Error ]: Could not connect to server")
        client_socket.close()
        return True

    init_payload = json.dumps({"type": "init", "connection_type": "chat"})
    client_socket.sendall(init_payload.encode())

    client_socket.setblocking(False)

    print(f"Connected to {HOST}:{port}. Start typing messages:")

    sel.register(sys.stdin, selectors.EVENT_READ)
    sel.register(client_socket, selectors.EVENT_READ)

    try:
        while True:
            # Wait for either user input or an incoming message from the server
            events = sel.select()
            for key, _ in events:
                if key.fileobj is sys.stdin:
                    # User typed something — read it and send to the server
                    message = sys.stdin.readline().strip()

                    if message:
                        # convert payload dict to json string
                        payload = json.dumps({"type": "chat_message", "message": message})

                        # send data encoded data to socket
                        client_socket.sendall(payload.encode())
                else:
                    # Server sent something — read and display it
                    data = client_socket.recv(4096)
                    if data:
                        print(data.decode())
                    else:
                        # Empty data means the server closed the connection
                        print("[ Exiting ] Server closed the connection")
                        return False
                    
    except KeyboardInterrupt:
        print("\n[ Disconnect ]: Closing chat")

    finally:
        sel.unregister(sys.stdin)
        sel.unregister(client_socket)
        client_socket.close()
        sel.close()
    
    return True


def chat_history(port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, port))
    except ConnectionRefusedError:
        print("[ Error ]: Could not connect to server")
        client_socket.close()
        return

    request_payload = json.dumps({"type": "init", "connection_type": "chat_history_request"})
    client_socket.sendall(request_payload.encode())

    print("===== Chat History =====")
    chunks = []

    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        chunks.append(data.decode())

    if not chunks:
        print("[ Info ]: No chat history found.")
    else:
        history_text = "".join(chunks)
        print(history_text, end="")
        if not history_text.endswith("\n"):
            print()

    print("========================")
    client_socket.close()


def print_menu():
    print("===== Chat Interface Menu =====")
    print("1. Enter Chat")
    print("2. Chat History")
    print("3. Exit")
    print("===============================")
    return


def main():
    port = parse_port_arg()

    try:
        while True:
            print_menu()
            user_input = input("Select an option: ")
            match user_input:
                case "1":
                    if chat_loop(port) == False: break 
                case "2":
                    chat_history(port)
                    continue
                case "3":
                    print("\n[ Exiting ]: Closing chat interface")
                    break
                case _:
                    print("User inputted an unavailable option")

    except KeyboardInterrupt:
        print("\n[ Exiting ]: Closing chat interface")


if __name__ == "__main__":
    main()
