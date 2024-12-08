from asyncio import (
    CancelledError,
    gather,
    run,
    start_server,
)
from struct import pack, unpack  # Used to pack and unpack data

# Server Configuration
HOST = ""  # All available interfaces
PORT = 12345  # Port to listen on (non-privileged ports are > 1023)
clients = {}  # List of connected clients
incremented_id = 0  # Incremented ID for each client
server_running = True  # This is used to stop the server


async def broadcast_message(message, sender_info=None) -> None:
    """
    Broadcasts a message to all connected clients
    """
    message_bytes = message.encode("utf-8")  # Encode the message to bytes
    message_length = pack("!H", len(message_bytes))  # Pack the message length
    # This is a tuple with the message length and the message, where [0] is the message length and [1] is the message
    message_and_header = (
        message_length + message_bytes
    )  # Concatenate the message length and the message

    tasks = []
    for client_info in clients.values():
        writer = client_info["writer"]
        # Only broadcast the message to clients that are not the sender
        if not sender_info or writer != sender_info[1]:
            try:
                writer.write(message_and_header)
                tasks.append(writer.drain())
            except Exception as e:
                print(f"Error Broadcasting Message: {e}")

    if tasks:
        await gather(*tasks, return_exceptions=True)


async def handle_client(reader, writer, user_name) -> None:
    """
    Handles a client connection
    """
    client_info = (reader, writer)
    # Add the client to the list of clients
    try:
        clients[user_name] = {
            "reader": reader,
            "writer": writer,
        }
        await broadcast_message(
            f"{user_name} has joined the chat!"
        )  # Broadcast that the client has joined the chat
        print(f"{user_name} has joined the chat!")

        while server_running:
            try:
                # Read the header data
                header_data = await reader.readexactly(2)
                if not header_data:
                    break

                # Read the message data
                message_length = unpack("!H", header_data)[
                    0
                ]  # We use [0] to get the first element of the tuple
                message_data = await reader.readexactly(message_length)
                if not message_data:
                    break

                # Process the message data
                message = message_data.decode(
                    "utf-8"
                )  # Decode the message data to a string from bytes
                await broadcast_message(
                    f"{user_name}: {message}", client_info
                )  # Broadcast the message to all clients
            except ConnectionError:
                print("Connection Error: The client has disconnected")
                break

    except CancelledError:
        print("Connection has been cancelled")
        pass
    except Exception as e:
        print(f"Error Handling Client: {e}")
    finally:
        if user_name in clients:
            del clients[user_name]
        try:
            writer.close()  # Close the client socket
            await writer.wait_closed()
        except Exception as e:
            print(f"Error Closing Client Connection: {e}")

        if server_running:
            await broadcast_message(f"{user_name} has left the chat!")
            print(f"{user_name} has left the chat!")


async def handle_connections():
    """
    Handles incoming client connections
    """
    global incremented_id

    server = await start_server(
        lambda read, write: handle_client(read, write, f"User {incremented_id}"),
        HOST,
        PORT,
    )

    async with server:
        print(f"Server listening on {HOST}:{PORT}")
        while server_running:
            try:
                incremented_id += 1
                await server.start_serving()
            except Exception as e:
                print(f"Error Handling Connections: {e}")
                break


async def stop_server():
    global server_running
    server_running = False
    print("\nStopping server...")
    print("Closing all client connections...")

    # Close all client connections
    close_messages = []
    for writer in clients.copy():
        try:
            writer.close()
            close_messages.append(writer.wait_closed())
        except Exception as e:
            print(f"Error Closing Client Connection: {e}")

    if close_messages:
        await gather(*close_messages, return_exceptions=True)

    clients.clear()
    print("All Client Connections Closed")


async def main() -> None:
    """
    Main function to start the server
    """
    try:
        await handle_connections()
    except KeyboardInterrupt:
        await stop_server()
    except Exception as e:
        print(f"Error Starting Server: {e}")
        await stop_server()


if __name__ == "__main__":
    print("Starting server...")
    print("Press Ctrl+C to stop the server")
    print("================================")
    try:
        run(main())
    except KeyboardInterrupt:
        print("\nServer Shutdown Complete")
