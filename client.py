import socket
import json
import sqlite3
import logging

# Configure logging (adjust log level and file path as needed)
logging.basicConfig(filename='client.log', level=logging.DEBUG)

SERVER_ADDRESS = "localhost"
SERVER_PORT = 5000
# Database file (update path as needed)
DATABASE_FILE = "./data/personnel.sqlite"

PERSONNEL_TABLE = """
CREATE TABLE IF NOT EXISTS personnel (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  surname TEXT NOT NULL,
  ssn TEXT NOT NULL UNIQUE
);
"""


def connect_to_database():
    connection = sqlite3.connect(DATABASE_FILE)
    return connection


def create_personnel_table(connection):
    cursor = connection.cursor()
    cursor.execute(PERSONNEL_TABLE)
    connection.commit()
    cursor.close()
    logging.info("Personnel table created (if it'd not exist).")


def save_personnel(connection, personnel):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO personnel (name, surname, ssn) VALUES (?, ?, ?)""",
            (personnel["name"], personnel["surname"], personnel["ssn"]),
        )
        connection.commit()
        logging.info(f"Personnel added: {personnel['name']} {personnel['surname']}")
    except sqlite3.IntegrityError as e:
        logging.error(f"Error adding personnel: {e} (probably duplicate SSN)")
    finally:
        cursor.close()


def delete_personnel(connection, personnel_id):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM personnel WHERE id = ?", (personnel_id,))
        connection.commit()
        logging.info(f"Personnel deleted with ID: {personnel_id}")
    except sqlite3.Error as e:
        logging.error(f"Error deleting personnel: {e}")
    finally:
        cursor.close()


def handle_message(connection, message):
    message_type = message["message_type"]
    payload = message["payload"]

    if message_type == "save":
        save_personnel(connection, payload)
    elif message_type == "delete":
        delete_personnel(connection, payload["id"])  # Assuming ID is used for deletion
    else:
        logging.warning(f"Unknown message type: {message_type}")


def main():
    connection = connect_to_database()
    create_personnel_table(connection)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_ADDRESS, SERVER_PORT))

    try:
        # Send client ID for server identification (optional)
        client_id = "client_1"  # Replace with actual client ID assignment logic
        message = {"message_type": "client_id", "payload": client_id}
        send_message(client_socket, message)

        while True:
            print("\nClient Menu:")
            print("1. Add new personnel")
            print("2. Request specific personnel")
            print("3. Exit")

            choice = input("Enter your choice: ")

            if choice == "1":
                # Get personnel information from user
                name = input("Enter name: ")
                surname = input("Enter surname: ")
                ssn = input("Enter SSN: ")

                # Create personnel data
                personnel = {"name": name, "surname": surname, "ssn": ssn}

                # Send "save" message with personnel data
                message = {"message_type": "save", "payload": personnel}
                send_message(client_socket, message)

            elif choice == "2":
                # Get personnel ID to request
                personnel_id = int(input("Enter personnel ID: "))

                # Send "request" message with personnel ID (consider adding a "message_type" for request)
                message = {"payload": {"id": personnel_id}}
                send_message(client_socket, message)

                # Wait for response from server (potentially display received personnel data)

            elif choice == "3":
                print("Exiting client...")
                break

            else:
                print("Invalid choice. Please try again.")

    except KeyboardInterrupt:
        logging.info("Client stopped by user.")
    finally:
        client_socket.close()
        connection.close()
        logging.info("Client connection closed.")


def send_message(client_socket, message):
    # Convert message to JSON and send
    json_message = json.dumps(message).encode()
    client_socket.sendall(json_message)


def receive_message(client_socket):
    message = client_socket.recv(1024).decode()
    return json.loads(message)


if __name__ == "__main__":
    main()
