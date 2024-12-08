from socket import AF_INET, SOCK_STREAM, socket  # Used to create a socket
from struct import pack, unpack  # Used to pack and unpack data
from threading import Thread  # Used to create a thread

# Server Configuration
HOST = ""  # All available interfaces
PORT = 12345  # Port to listen on (non-privileged ports are > 1023)
clients = []  # List of connected clients
incremented_id = 0  # Incremented ID for each client


def broadcast_message(message, sender_socket=None) -> None:
    """
    Broadcasts a message to all connected clients

    What happens here?
    ===================
    1. Pack the message length
    2. Concatenate the message length and the message to create the message and header
    3. Loop through all clients
    4. Check if the client is not the sender
    5. Send the message to the client
    6. If an error occurs, print the error
    7. If the client has disconnected, remove the client from the list of clients
    """
    message_bytes = message.encode("utf-8")  # Encode the message to bytes
    message_length = pack("!H", len(message_bytes))  # Pack the message length
    # This is a tuple with the message length and the message, where [0] is the message length and [1] is the message
    message_and_header = (
        message_length + message_bytes
    )  # Concatenate the message length and the message
    for client in clients:
        if client != sender_socket:  # Don't send the message to the sender
            try:
                client.sendall(message_and_header)  # Send the message to the client
            except Exception as e:
                print(f"Error: {e}")
                if client in clients:
                    clients.remove(client)


def handle_client(client_socket, user_name) -> None:
    """
    Handles a client connection

    What happens here?
    ===================

    1. Add the client to the list of clients
    2. Broadcast that the client has joined the chat
    3. Receive messages from the client
    4. Broadcast the message to all clients
    5. If an error occurs, print the error
    6. If the client has disconnected, remove the client from the list of clients and close the client socket
    7. Broadcast that the client has left the chat
    """
    # Add the client to the list of clients
    try:
        broadcast_message(
            f"{user_name} has joined the chat!", client_socket
        )  # Broadcast that the client has joined the chat
        print(f"{user_name} has joined the chat!")
        while True:  # Loop to receive messages from the client
            header_data = client_socket.recv(2)  # Receive the header data
            # Check if the client has disconnected
            if not header_data:
                break
            message_length = unpack("!H", header_data)[
                0
            ]  # We use [0] to get the first element of the tuple
            message_data = client_socket.recv(
                message_length
            )  # Receive the message data. We use the message length to know how much data to receive
            # Check if the client has disconnected
            if not message_data:
                break
            message = message_data.decode(
                "utf-8"
            )  # Decode the message data to a string from bytes
            broadcast_message(
                f"\n{user_name}: {message}", client_socket
            )  # Broadcast the message to all clients
    # If an error occurs
    except Exception as e:
        print(f"Error: {e}")
    # If the client has disconnected
    finally:
        clients.remove(client_socket)  # Remove the client from the list of clients
        client_socket.close()  # Close the client socket
        broadcast_message(f"{user_name} has left the chat!")


def main() -> None:
    """
    Main function to start the server

    What happens here?
    ===================
    1. Create a TCP socket
    2. Bind the server socket to the host and port
    3. Listen for incoming connections
    4. Loop to accept incoming connections
    5. Accept the incoming connection
    6. Increment the ID for the next client
    7. Add the client to the list of clients
    8. Send the length of the user name and the user name to the client
    9. Create a thread to handle the client
    10. Start the thread
    11. If an error occurs, print the error and close all client sockets and the server socket
    12. If the server is stopped, print a message and close all client sockets and the server socket
    """
    global incremented_id
    # Create a TCP socket
    with socket(AF_INET, SOCK_STREAM) as server_socket:
        # Bind the server socket to the host and port
        server_socket.bind((HOST, PORT))
        # Listen for incoming connections
        server_socket.listen()
        print(f"Server listening on {HOST}:{PORT}")
        try:
            while True:  # Loop to accept incoming connections
                # client_address is the address of the client but we don't need it
                # if we did we would use it to send data back to the client
                client_socket, client_address = (
                    server_socket.accept()
                )  # Accept the incoming connection
                user_name = f"User {incremented_id}"  # Incremented ID for each client
                incremented_id += 1  # Increment the ID for the next client
                clients.append(client_socket)  # Add the client to the list of clients
                client_socket.sendall(
                    pack("!H", len(user_name)) + user_name.encode("utf-8")
                )  # Send the length of the user name and the user name to the client
                # target is the function to be called when the thread starts
                # args is a tuple with the arguments to be passed to the target function
                thread = Thread(
                    target=handle_client, args=(client_socket, user_name)
                )  # Create a thread to handle the client
                thread.start()  # Start the thread
        except KeyboardInterrupt:
            print("\nStopping server...")
            print("Closing all client connections...")
            for client in clients:
                client.close()
            server_socket.close()
        # If an error occurs, print the error and close all client sockets and the server socket
        except Exception as e:
            print(f"Error: {e}")
            for client in clients:
                client.close()  # Close all client sockets
            server_socket.close()  # Close the server socket


if __name__ == "__main__":
    print("Starting server...")
    print("Press Ctrl+C to stop the server")
    print("================================")
    main()
