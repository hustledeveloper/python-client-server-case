import socket
import json
import sqlite3
import logging
import threading
import mysql.connector


SERVER_ADDRESS = "localhost"
SERVER_PORT = 5000
HOST_DB = "localhost"
USER_DB = "user"
PASSWORD_DB = "password"
DATABASE_DB = "db"


def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=HOST_DB,
            user=USER_DB,
            password=PASSWORD_DB,
            database=DATABASE_DB,
        )
        print("Connected to MySQL database!")
        return connection
    except mysql.connector.Error as err:
        print("Error connecting:", err)
        return None


def create_tables():
    connection = connect_to_database()
    cursor = connection.cursor()

    create_clients_table = """
    CREATE TABLE IF NOT EXISTS clients (
        id INT NOT NULL AUTO_INCREMENT,
        ip_address VARCHAR(255) NOT NULL,
        port INT NOT NULL,
        PRIMARY KEY (id)
    );
    """
    cursor.execute(create_clients_table)

    create_personnel_table = """
    CREATE TABLE IF NOT EXISTS personnel (
        id INT NOT NULL AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        surname VARCHAR(255) NOT NULL,
        ssn VARCHAR(255) NOT NULL,
        PRIMARY KEY (id)
    );
    """
    cursor.execute(create_personnel_table)

    create_messages_table = """
    CREATE TABLE IF NOT EXISTS messages (
        id INT NOT NULL AUTO_INCREMENT,
        client_id INT NOT NULL,
        message_type VARCHAR(255) NOT NULL,
        payload TEXT NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(id),
        PRIMARY KEY (id)
    );
    """
    cursor.execute(create_messages_table)

    connection.commit()
    cursor.close()
    connection.close()
    print("Tables created (if they don't exist) in the database.")


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


def get_all_personnel(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM personnel")
    personnel = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return personnel


def get_personnel_by_id(connection, personnel_id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM personnel WHERE id = ?", (personnel_id,))
    personnel = cursor.fetchone()
    if personnel:
        return dict(personnel)
    else:
        return None
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


def delete_all_personnel(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM personnel")
        connection.commit()
        logging.info("All personnel deleted.")
    except sqlite3.Error as e:
        logging.error(f"Error deleting all personnel: {e}")
    finally:
        cursor.close()


def send_message(client_socket, message):
    # Convert message to JSON and send
    json_message = json.dumps(message).encode()
    client_socket.sendall(json_message)


def receive_message(client_socket):
    message = client_socket.recv(1024).decode()
    return json.loads(message)


def handle_client(connection, client_socket):
    while True:
        message = receive_message(client_socket)
        message_type = message["message_type"]
        payload = message["payload"]

        if message_type == "client_id":
            client_id = payload
            logging.info(f"Client {client_id} connected.")
            break  # Exit loop after receiving client ID

    while True:
        try:
            # Display server options
            print("\nServer Options:")
            print("1. Send specific personnel to a specific client")
            print("2. Send specific personnel to all clients")
            print("3. Send all personnel to all clients")
            print("4. Delete specific personnel from a specific client")
            print("5. Delete specific personnel from all clients")
            print("6. Delete all personnel from all clients")
            print("q. Quit")

            choice = input("Enter your choice: ")

            if choice.lower() == "q":
                break

            if choice == "1":
                # Get target client ID and personnel ID
                target_client_id = input("Enter target client ID: ")
                personnel_id = int(input("Enter personnel ID to send: "))
                personnel = get_personnel_by_id(connection, personnel_id)

                if personnel:
                    message = {"message_type": "save", "payload": personnel}
                    send_message(client_sockets[target_client_id], message)
                    logging.info(f"Personnel sent to client {target_client_id}")
                else:
                    print(f"Personnel with ID {personnel_id} not found.")

            elif choice == "2":
                # Get personnel ID
                personnel_id = int(input("Enter personnel ID to send: "))
                personnel = get_personnel_by_id(connection, personnel_id)

                if personnel:
                    message = {"message_type": "save", "payload": personnel}
                    for client_socket in client_sockets.values():
                        send_message(client_socket, message)
                    logging.info(f"Personnel sent to all clients.")
                else:
                    print(f"Personnel with ID {personnel_id} not found.")

            elif choice == "3":
                # Send all personnel to all clients
                all_personnel = get_all_personnel(connection)
                message = {"message_type": "save", "payload": all_personnel}
                for client_socket in client_sockets.values():
                    send_message(client_socket, message)
                logging.info("All personnel sent to all clients.")

            elif choice == "4":
                # Get target client ID and personnel ID
                target_client_id = input("Enter target client ID: ")
                personnel_id = int(input("Enter personnel ID to delete: "))

                delete_personnel(connection, personnel_id)
                message = {"message_type": "delete", "payload": {"id": personnel_id}}
                send_message(client_sockets[target_client_id], message)
                logging.info(f"Personnel deleted from client {target_client_id}.")

            elif choice == "5":
                # Get personnel ID
                personnel_id = int(input("Enter personnel ID to delete: "))

                delete_personnel(connection, personnel_id)
                message = {"message_type": "delete", "payload": {"id": personnel_id}}
                for client_socket in client_sockets.values():
                    send_message(client_socket, message)
                logging.info(f"Personnel deleted from all clients.")

            elif choice == "6":
                # Delete all personnel from all clients
                delete_all_personnel(connection)
                message = {"message_type": "delete", "payload": {"all": True}}
                for client_socket in client_sockets.values():
                    send_message(client_socket, message)
                logging.info("All personnel deleted from all clients.")

        except Exception as e:
            logging.error(f"Error handling client: {e}")


def main():
    connection = connect_to_database()
    create_tables()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDRESS, SERVER_PORT))
    server_socket.listen()

    logging.info("Server listening on {}:{}".format(SERVER_ADDRESS, SERVER_PORT))

    client_sockets = []  # List to store dictionaries with client ID and socket

    while True:
        client_socket, client_address = server_socket.accept()
        logging.info("New connection from {}".format(client_address))

        # Handle new client in a separate thread
        thread = threading.Thread(target=handle_client, args=(connection, client_socket))
        thread.start()  # Start thread before accessing client_sockets

        # Receive client ID from the client
        message = receive_message(client_socket)
        client_id = message["payload"]

        # Create a dictionary for client information
        client_info = {"client_id": client_id, "client_socket": client_socket}

        # Append client information to the list
        client_sockets.append(client_info)

        # Notify other clients about the new connection (optional)
        # ...

if __name__ == "__main__":
    main()
