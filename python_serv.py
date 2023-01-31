import socket
import json
import sqlite3
import threading
from typing import List, Tuple
import time
import sys

from pprint import pprint

from tkinter import *
from tkinter import ttk


class Server:
    def __init__(self, master: Tk, address: str, port: int):

        self.threads = []
        self.run_thread = True

        self.master = master
        self.address = address
        self.port = port

        self.log_area = Text(self.master)

        try:
            self.db = sqlite3.connect("bdd.sqlite", check_same_thread=False)
            self.cursor = self.db.cursor()
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS users(username TEXT, ip TEXT)"
            )

            # On vide la table avant de commencer
            self.cursor.execute("DELETE FROM users")
            self.db.commit()
            self.log_area.insert(
                END,
                "Connecté à la BDD\n",
            )

        except:
            self.log_area.insert(
                END,
                "Connexion à la BDD échouée\n",
            )

        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.listener.bind((self.address, self.port))
            self.listener.listen(5)
            self.log_area.insert(
                END,
                f"En écoute sur {self.address}:{self.port}\n",
            )
        except socket.error as e:
            print(f"Error binding to address {self.address} and port {self.port}: {e}")
            self.log_area.insert(
                END,
                f"Erreur pour se lier à {self.address}:{self.port}: {e}\n",
            )
            self.listener.close()

        thread = threading.Thread(target=self.accept_connections, daemon=True)
        thread.start()
        self.log_area.insert(
            END,
            "Lancement Thread accept_connections\n",
        )
        self.threads.append(thread)

        self.label = ttk.Label(
            self.master, text=f"Listening on {self.address}:{self.port}"
        )
        self.label.pack()
        self.log_area.pack()

        self.close_button = ttk.Button(self.master, text="Close", command=self.close)
        self.close_button.pack()

        # Add a small frame on the server window to live view the content of the database

        self.db_frame = ttk.Frame(self.master)
        self.db_frame.pack()

        # Add a Treeview widget to the frame and bind it to a scrollbar
        self.db_tree = ttk.Treeview(self.db_frame, height=5)
        self.db_scroll = ttk.Scrollbar(
            self.db_frame, orient="vertical", command=self.db_tree.yview
        )
        self.db_tree.configure(yscrollcommand=self.db_scroll.set)

        # Set the columns of the Treeview widget
        self.db_tree["columns"] = "ip"
        self.db_tree.column("#0", width=100, minwidth=100)
        self.db_tree.column("ip", width=100, minwidth=100)
        self.db_tree.heading("#0", text="Name")
        self.db_tree.heading("ip", text="IP")

        # Pack the Treeview widget and the scrollbar
        self.db_tree.pack(side="left")
        self.db_scroll.pack(side="right", fill="y")

        # Update the Treeview widget with the content of the database in a separate thread
        thread2 = threading.Thread(target=self.update_db_tree)
        thread2.start()
        self.threads.append(thread2)

    def update_db_tree(self):
        while self.run_thread:
            # Clear the Treeview widget
            for i in self.db_tree.get_children():
                self.db_tree.delete(i)

            # Retrieve the content of the database
            self.cursor.execute("SELECT * FROM users")
            rows = self.cursor.fetchall()

            # Add the rows to the Treeview widget
            for row in rows:
                self.db_tree.insert("", "end", text=row[0], values=(row[1],))

            # Sleep for 1 second before updating the Treeview widget again
            time.sleep(1)

    def accept_connections(self):
        while self.run_thread:
            try:
                client, address = self.listener.accept()
                # Create a new thread for each client connection and start the thread.
                thread = threading.Thread(
                    target=self.handle_client, args=(client, address)
                )
                thread.start()
                self.threads.append(thread)
            except Exception as e:
                pass

    def delete_user(self, name: str):
        print(name)
        self.cursor.execute(f'DELETE FROM users WHERE username="{name}"')
        self.db.commit()

    def handle_client(self, client: socket.socket, address: Tuple[str, int]):
        try:
            while self.run_thread:
                data = client.recv(1024)
                data = json.loads(data.decode())
                self.client_name = data["name"]

                if data["command"] == "REG":
                    try:
                        response = self.register_user(data["name"], address[0])
                        if response:
                            response = {"ack": "Registered successfully"}
                            self.log_area.insert(
                                END,
                                f"Registered user {data['name']} with IP {address[0]}\n",
                            )
                        else:
                            response = {"ack": "Error Registering"}
                            self.log_area.insert(
                                END,
                                f"User {data['name']} already registered with IP {address[0]}\n",
                            )
                    except Exception as e:
                        response = {"ack": "Error"}
                        self.log_area.insert(
                            END, f"Error registering user {data['name']} : {e} \n"
                        )
                elif data["command"] == "GET":
                    self.log_area.insert(
                        END,
                        f"L'utilisateur {self.client_name} souhaite joindre {data['name']}\n",
                    )
                    result = self.get_ip(data["name"])
                    if result is None:
                        response = {"ip": "None"}
                        self.log_area.insert(
                            END,
                            f"{data['name']} est inconnu du système\n",
                        )
                    else:
                        response = {"ip": result}
                        response = {"ip": "None"}
                        self.log_area.insert(
                            END,
                            f"{data['name']} est à l'ip : {response}\n",
                        )

                elif data["command"] == "DISCONNECT":
                    self.delete_user(data["name"])

                print(response)
                client.send(json.dumps(response).encode())

        except Exception as e:
            try:
                # Handle any exceptions that may occur while handling the client's request
                self.delete_user(data["name"])
            except:
                pass
            self.log_area.insert(END, f"{data['name']} disconnected\n")

    def register_user(self, name: str, ip: str):
        self.cursor.execute(f'SELECT * FROM users WHERE username="{name}"')
        result = self.cursor.fetchone()

        if result is not None:
            return False

        self.cursor.execute("INSERT INTO users(username, ip) VALUES (?, ?)", (name, ip))
        self.db.commit()
        return True

    def get_ip(self, name: str):
        self.cursor.execute("SELECT * FROM users WHERE username=?", (name,))
        result = self.cursor.fetchone()

        if result is None:
            return None

        return result[1]

    def close(self):
        # Disable new incoming connections
        self.run_thread = False
        if self.listener:
            self.listener.close()
        self.db.close()
        self.master.destroy()
        sys.exit()


if __name__ == "__main__":
    root = Tk()
    root.title("Server")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    serv_adress = s.getsockname()[0]

    server = Server(root, serv_adress, 10000)
    root.mainloop()
