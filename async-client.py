import sys
from asyncio import (
    FIRST_COMPLETED,
    CancelledError,
    create_task,
    open_connection,
    run,
    wait,
)
from struct import pack, unpack

from aioconsole import ainput


async def recv_all(reader, size):
    """
    Receives messages from the server
    """
    message = b""  # Initialize the data variable that will store the received data
    while len(message) < size:  # Loop until the data length is equal to the size
        packet = await reader.read(size - len(message))  # Receive the data
        if not packet:
            raise ConnectionError("Connection to Server Lost")
        message += packet  # Add the packet data to the message
    return message


async def receive_messages(reader):
    """
    Receives messages from the server
    """
    try:
        while True:
            # Read the header data from the server
            header_data = await recv_all(reader, 2)
            message_length = unpack("!H", header_data)[
                0
            ]  # Unpack the message length from the header data

            # Read the message data from the server
            message_data = await recv_all(
                reader, message_length
            )  # Receive the message from the server
            message = message_data.decode(
                "utf-8"
            )  # Decode the message data to a string from bytes

            # Clear the current line and reprompt the user for input
            print("\r" + " " * 100, end="\r")
            print(message, end="")
            print("\nYou: ", end="")

    except ConnectionError:
        print("\nConnection Error: The server has disconnected")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print(
            "\nDisconnected from the server"
        )  # Print that the client has disconnected from the server
        sys.exit(0)


async def send_message(writer):
    try:
        while True:
            message = await ainput("You: ")

            if message:
                # Send the Message
                message_data = message.encode("utf-8")
                message_length = pack("!H", len(message_data))
                writer.write(message_length + message_data)
                await writer.drain()

    except CancelledError:
        print("Connection has been cancelled")
        sys.exit(1)
    except ConnectionError:
        print("Connection Error: The server has disconnected")
        sys.exit(1)
    except Exception as e:
        print(f"Error Sending Message: {e}")
        sys.exit(1)


async def main():
    try:
        # Connect to the server
        server_address = ("localhost", 12345)
        reader, writer = await open_connection(*server_address)

        # Receive Username
        user_name_length = await recv_all(reader, 2)
        user_name_length = unpack("!H", user_name_length)[0]
        user_name_data = await recv_all(reader, user_name_length)
        user_name = user_name_data.decode("utf-8")
        print(f"Connected to the server as {user_name}")

        # Create tasks to send/receive messages
        receive_task = create_task(receive_messages(reader))
        send_task = create_task(send_message(writer))

        # Wait for the tasks to complete
        sent, pending = await wait(
            [receive_task, send_task], return_when=FIRST_COMPLETED
        )

        # Cancel the pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except CancelledError:
                pass
    except ConnectionRefusedError:
        print("Connection Error: The server is not running")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            # Clean up the connection
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    print("Starting the client")
    print("Press Ctrl+C to exit")
    try:
        run(main())
    except KeyboardInterrupt:
        print("\nExiting the client")
    except Exception as e:
        print(f"\nAn error occurred {e}")
