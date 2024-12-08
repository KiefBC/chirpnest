import os
import sys
from socket import AF_INET, SOCK_STREAM, socket
from struct import pack, unpack
from threading import Thread


def recv_all(socket, size):
    """
    Receives messages from the server

    What happens here?
    ===================
    1. Initialize the data variable that will store the received data
    2. Loop until the data length is equal to the size
    3. Receive the data
    4. Check if the client has disconnected
    5. Add the packet data to the message
    6. Return the message
    """
    message = b""  # Initialize the data variable that will store the received data
    while len(message) < size:  # Loop until the data length is equal to the size
        packet = socket.recv(size - len(message))  # Receive the data
        # Check if the client has disconnected
        # If the client has disconnected, raise a ConnectionError
        if not packet:
            raise ConnectionError("The client has disconnected")
        message += packet  # Add the packet data to the message
    return message


def receive_messages(client_socket):
    """
    Receives messages from the server

    What happens here?
    ===================
    1. Loop forever
    2. Receive the header data from the server
    3. Unpack the message length from the header data
    4. Receive the message from the server
    5. Decode the message data to a string from bytes
    6. Print the message from the server
    7. If an error occurs, print the error
    8. Close the client socket
    """
    try:
        while True:
            header_data = recv_all(
                client_socket, 2
            )  # Receive the header data from the server
            message_length = unpack("!H", header_data)[
                0
            ]  # Unpack the message length from the header data
            message_data = recv_all(
                client_socket, message_length
            )  # Receive the message from the server
            message = message_data.decode(
                "utf-8"
            )  # Decode the message data to a string from bytes

            # Clear the current line and reprompt the user for input
            print("\r", end="")
            print(" " * 100, end="")
            print("\r", end="")
            print(message, end="")
            print("\nYou: ", end="")

    except ConnectionError:
        print("Connection Error: The server has disconnected")
        os._exit(0)
    except Exception as e:
        print(f"Error: {e}")
        os._exit(0)
    finally:
        print(
            "Disconnected from the server"
        )  # Print that the client has disconnected from the server
        client_socket.close()  # Close the client socket
        os._exit(0)


def main():
    server_address = ("localhost", 12345)
    try:
        with socket(AF_INET, SOCK_STREAM) as client_socket:
            client_socket.connect(server_address)
            # user_name = input("Enter your name: ")
            user_name_length = recv_all(client_socket, 2)
            name_length_data = unpack("!H", user_name_length)[0]
            user_name_data = recv_all(client_socket, name_length_data)
            user_name = user_name_data.decode("utf-8")
            print(f"Welcome to the chat, {user_name}!")
            receive_thread = Thread(
                target=receive_messages, args=(client_socket,), daemon=True
            )
            receive_thread.start()
            while True:
                try:
                    message = input("You: ")
                    if message:
                        message_data = message.encode("utf-8")
                        message_length = pack("!H", len(message_data))
                        client_socket.sendall(message_length + message_data)
                except KeyboardInterrupt:
                    print("\nDisconnected from the server")
                    break
                except ConnectionError:
                    print("\nConnection Error: The server has disconnected")
                    os._exit(0)
                except Exception as e:
                    print(f"Error: {e}")
                    os._exit(0)
    except ConnectionRefusedError:
        print("Connection Error: The server refused the connection")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        try:
            client_socket.close()
        except:
            pass
        os._exit(0)


if __name__ == "__main__":
    print("Starting the client")
    print("Press Ctrl+C to exit")
    main()
