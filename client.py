import json
import socket
import threading
from typing import Dict, List, Optional, Tuple
import re

import pyaudio
import tkinter as tk


class Client(tk.Tk):
    """A softphone client that uses tkinter for the GUI and pyaudio for audio recording and transmission.

    This class handles the connection to the server, the GUI, and the audio transmission.
    """

    def __init__(self):
        """Initializes the GUI and the sockets for the connection to the server and for the audio transmission."""
        tk.Tk.__init__(self)
        self.server_ip: Optional[str] = None
        self.server_port: Optional[int] = None
        self.client_name: Optional[str] = None
        self.listening_for_calls = False
        self.caller_ip = None
        self.call_in_progress = False
        self.connexion_serveur = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Compte tenu de la rapidité des réseaux aujourd'hui, un timeout d'une seconde n'est pas de trop
        self.server_socket.settimeout(1)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.udp_socket.bind(("", 5001))
        except socket.error as e:
            print(f"Error binding to port 5001 : {e}")
            self.udp_socket.close()

        # Initialize the pyaudio recording and playback objects.
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.FREQUENCE = 8000  # en Hertz
        self.NB_ECHANTILLONS = 512
        self.pyaudio = pyaudio.PyAudio()
        self.input_stream = self.pyaudio.open(
            format=self.FORMAT, channels=self.CHANNELS, rate=self.FREQUENCE, input=True
        )
        self.output_stream = self.pyaudio.open(
            format=self.FORMAT, channels=self.CHANNELS, rate=self.FREQUENCE, output=True
        )

        # Create the GUI elements and set their position and behavior.
        self.title("Client")
        self.log_text = tk.Text(self, width=50, height=10)
        self.log_text.pack()

        self.config_frame = tk.Frame(self)
        self.config_frame.pack()
        self.server_ip_label = tk.Label(self.config_frame, text="Server IP:")
        self.server_ip_label.pack(side="left")
        self.server_ip_entry = tk.Entry(self.config_frame)
        self.server_ip_entry.pack(side="left")
        self.server_ip_entry.insert(0, "192.168.38.169")
        self.server_port_label = tk.Label(self.config_frame, text="Server port:")
        self.server_port_label.pack(side="left")
        self.server_port_entry = tk.Entry(self.config_frame)
        self.server_port_entry.pack(side="left")
        self.server_port_entry.insert(0, "10000")
        self.client_name_label = tk.Label(self.config_frame, text="Client name:")
        self.client_name_label.pack(side="left")
        self.client_name_entry = tk.Entry(self.config_frame)
        self.client_name_entry.pack(side="left")
        self.config_button = tk.Button(
            self.config_frame, text="Configure", command=self.configure
        )
        self.config_button.pack(side="left")
        self.bind("<Return>", self.configure)

        self.call_frame = tk.Frame(self)
        self.call_frame.pack()
        self.call_name_label = tk.Label(self.call_frame, text="Call to:")
        self.call_name_label.pack(side="left")
        self.call_name_entry = tk.Entry(self.call_frame)
        self.call_name_entry.pack(side="left")
        self.call_button = tk.Button(
            self.call_frame, text="Call", command=self.call, state=tk.DISABLED
        )
        self.call_button.pack(side="left")

        self.btn_raccrocher = tk.Button(
            self, text="Raccrocher", command=self.raccrocher, state=tk.DISABLED
        )
        self.btn_raccrocher.pack()

        self.close_button = tk.Button(self, text="Close", command=self.close)
        self.close_button.pack()

        self.log_text.tag_config("avertissement", foreground="red")

    def configure(self, *args) -> None:
        """Configures the connection to the server using the information entered in the GUI."""
        server_ip = self.server_ip_entry.get()
        server_port = self.server_port_entry.get()
        self.client_name = self.client_name_entry.get().strip()

        ip_regex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"

        if (
            re.match(ip_regex, server_ip)
            and int(server_port) > 1024
            and int(server_port) < 65535
            and self.client_name != ""
        ):
            # L'entrée est valide, on peut continuer à configurer la connexion
            self.server_ip = server_ip
            self.server_port = int(server_port)
            self.log_text.insert(
                tk.END,
                f"Connexion à {self.server_ip}:{self.server_port} en tant que {self.client_name}\n",
            )
            try:
                # Connect to the server and send the client's name to register it in the server's database.
                self.server_socket.connect((self.server_ip, self.server_port))
            except TimeoutError:
                self.log_text.insert(
                    tk.END,
                    "TimeoutError, le serveur n'a pas répondu à temps\n",
                    "avertissement",
                )
                return
            except Exception as e:
                self.log_text.insert(
                    tk.END,
                    f"Erreur : {e}\n",
                    "avertissement",
                )
                return

            data = json.dumps({"command": "REG", "name": self.client_name}).encode(
                "utf-8"
            )
            self.server_socket.sendall(data)
            print("Envoi de :", data, " au serveur")
            response = self.server_socket.recv(1024).decode("utf-8")
            print("Réponse du serveur : ", response)
            # self.log_text.insert(tk.END, f"{response}\n")
            response_data = json.loads(response)
            if response_data["ack"] == "Registered successfully":
                self.log_text.insert(tk.END, "Enregistrement réussi\n")
                self.connexion_serveur = True
                self.call_button["state"] = tk.NORMAL
            else:
                self.log_text.insert(
                    tk.END,
                    f"Impossible de s'enregistrer sur le serveur: {response_data['ack']}\n",
                    "avertissement",
                )

            # Start listening for incoming call requests in a separate thread.
            threading.Thread(target=self.listen_for_call_requests, daemon=True).start()
            self.config_button["state"] = tk.DISABLED

        elif not re.match(ip_regex, server_ip):
            # L'entrée n'est pas valide, on peut afficher un message d'erreur
            self.log_text.insert(
                tk.END, "L'adresse IP du serveur est invalide", "avertissement"
            )

        elif isinstance(server_port, int):
            self.log_text.insert(
                tk.END,
                "Le numéro de port est invalide, ce doit être un nombre compris entre 1024 et 65535",
                "avertissement",
            )

        elif not (int(server_port) > 1024 and int(server_port) < 65535):
            self.log_text.insert(
                tk.END,
                "Le numéro de port doit être compris entre 1024 et 65535",
                "avertissement",
            )
        elif self.client_name == "":
            self.log_text.insert(
                tk.END,
                "Vous devez entrer un nom",
                "avertissement",
            )

    def call(self) -> None:
        """Initiates a call to the client with the specified name entered in the GUI.

        This method first sends a GET request to the server to retrieve the IP address of the client
        to be called. Then it sends a START request to the called client, containing the caller's name.
        """

        print("-----------------")
        called_client_name = self.call_name_entry.get()
        if (
            called_client_name.strip() != ""
        ):  # https://stackoverflow.com/questions/9573244/how-to-check-if-the-string-is-empty/27982561#27982561

            # Send a GET request to the server to retrieve the IP address of the called client.
            self.server_socket.sendall(
                json.dumps({"command": "GET", "name": called_client_name}).encode(
                    "utf-8"
                )
            )
            response = self.server_socket.recv(1024).decode("utf-8")
            response_data = json.loads(response)
            called_client_ip = response_data.get("ip")

            # If the called client's IP was successfully retrieved, send a START request to initiate the call.
            if called_client_ip != None:
                self.udp_socket.sendto(
                    f"START {self.client_name}".encode("utf-8"),
                    (called_client_ip, 5001),
                )
                self.log_text.insert(
                    tk.END,
                    f"Appel à {called_client_name} sur {called_client_ip}\n",
                )
            else:
                self.log_text.insert(
                    tk.END,
                    f"Impossible d'appeler: {called_client_name} est inconnu de l'annuaire\n",
                    "avertissement",
                )

            answer = ""
            self.udp_socket.settimeout(7)
            while answer == "":
                try:
                    data, addr = self.udp_socket.recvfrom(1024)
                    answer = data.decode("utf-8")
                    print(answer)
                    break
                # pas de décodage possible si donnée vocale
                except socket.timeout:
                    threading.Thread(target=self.listen_for_call_requests())
                    return

                except Exception as e:
                    print("décodage impossible", e)
                    pass

            if answer.startswith("ACCEPT"):
                self.call_in_progress = True
                self.transmit_audio(called_client_ip)
                self.btn_raccrocher["state"] = tk.NORMAL

            elif answer.startswith("REJECT"):
                threading.Thread(
                    target=self.listen_for_call_requests, daemon=True
                ).start()
        else:
            self.log_text.insert(
                tk.END, f"Recipient's name is empty\n", "avertissement"
            )

    def listen_for_call_requests(self) -> None:
        """Listens for incoming call requests and opens a new window to accept or reject the call.

        This method runs in a separate thread, continuously listening on port 5001 for incoming call
        requests. If a call request is received, it opens a new window with accept and reject buttons,
        and waits for the user to accept or reject the call. If the call is accepted, it sends an ACCEPT
        message to the caller and starts transmitting audio data.
        """
        self.log_text.insert(tk.END, "Mise en écoute\n")
        self.listening_for_calls = True
        while self.listening_for_calls:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                data = data.decode("utf-8")
                if data.startswith("START"):
                    name = data.split(" ")[1]
                    self.log_text.insert(tk.END, f"Appel reçu de {name}\n")
                    IncomingCallWindow(self, name)
                    self.listening_for_calls = False
            except:
                pass

    def accept_call(self, caller_name: str) -> None:
        """Accepts an incoming call request and starts transmitting audio data.

        This method is called when the user clicks the accept button in the incoming call window. It
        sends an ACCEPT message to the caller, closes the incoming call window, and starts transmitting
        audio data in a separate thread.
        """
        self.listening_for_calls = False
        self.call_in_progress = True
        self.log_text.insert(tk.END, f"Call from {caller_name} accepted\n")
        self.btn_raccrocher["state"] = tk.NORMAL

        # Send an ACCEPT message to the caller.
        self.server_socket.sendall(
            json.dumps({"command": "GET", "name": caller_name}).encode("utf-8")
        )
        response = self.server_socket.recv(1024).decode("utf-8")
        response_data = json.loads(response)
        self.caller_ip = response_data.get("ip")

        # If the caller's IP was successfully retrieved, start transmitting audio data.
        if self.caller_ip:
            for _ in range(10):
                self.udp_socket.sendto("ACCEPT".encode("utf-8"), (self.caller_ip, 5001))
            self.transmit_audio(self.caller_ip)
        else:
            self.log_text.insert(
                tk.END,
                f"Error starting call with {caller_name}: {caller_name} does not exist or is offline\n",
                "avertissement",
            )

    def reject_call(self, caller_name: str) -> None:
        """Rejects an incoming call request.

        This method is called when the user clicks the reject button in the incoming call window, or
        when the incoming call window is closed. It sends a REJECT message to the caller and closes the
        incoming call window.
        """
        self.listening_for_calls = True
        self.log_text.insert(tk.END, f"Call from {caller_name} rejected\n")

        # Send a REJECT message to the caller.
        self.server_socket.sendall(
            json.dumps({"command": "GET", "name": caller_name}).encode("utf-8")
        )
        response = self.server_socket.recv(1024).decode("utf-8")
        response_data = json.loads(response)
        if "ip" in response_data:
            self.caller_ip = response_data["ip"]
            self.udp_socket.sendto("REJECT".encode("utf-8"), (self.caller_ip, 5001))
        else:
            self.log_text.insert(
                tk.END,
                f"Error rejecting call with {caller_name}: {caller_name} does not exist or is offline\n",
                "avertissement",
            )
        self.listening_for_calls = True
        self.listen_for_call_requests()

    def transmit_audio(self, caller_ip: str) -> None:
        """Transmits audio data from the input stream to the recipient's IP address.

        This method is called in a separate thread when a call is accepted. It continuously reads
        audio data from the input stream and sends it to the recipient's IP address using the UDP
        socket. It also listens for incoming audio data on port 5001 and plays it through the output
        stream."""

        self.caller_ip = caller_ip

        def read_audio():
            while self.call_in_progress:
                # Read audio data from the input stream and send it to the recipient.
                data = self.input_stream.read(self.NB_ECHANTILLONS)
                self.udp_socket.sendto(data, (self.caller_ip, 5001))

        def write_audio():
            while self.call_in_progress:
                try:
                    # Listen for incoming audio data and play it through the output stream.
                    data, addr = self.udp_socket.recvfrom(self.NB_ECHANTILLONS * 2)
                    if data.decode("utf-8").startswith("CLOSE"):
                        self.raccrocher()
                        return
                except:
                    self.output_stream.write(data)

        # Create and start the two threads
        read_thread = threading.Thread(target=read_audio, daemon=True)
        write_thread = threading.Thread(target=write_audio, daemon=True)
        read_thread.start()
        write_thread.start()

    def raccrocher(self) -> None:
        """Disconnects from the other client."""
        if self.call_in_progress:
            self.call_in_progress = False
            try:
                self.input_stream.stop_stream()
                self.output_stream.stop_stream()
                self.input_stream.close()
                self.output_stream.close()
            except:
                pass
            for _ in range(5):
                self.udp_socket.sendto("CLOSE".encode("utf-8"), (self.caller_ip, 5001))
            self.log_text.insert(tk.END, "Appel terminé\n")
            self.btn_raccrocher["state"] = tk.DISABLED
            self.listening_for_calls = True
            threading.Thread(target=self.listen_for_call_requests)

    def close(self) -> None:
        """Closes the client's GUI window."""
        self.raccrocher()
        if self.connexion_serveur:
            data = json.dumps(
                {"command": "DISCONNECT", "name": self.client_name}
            ).encode("utf-8")
            self.server_socket.sendto(data, (self.server_ip, self.server_port))
            self.server_socket.close()
        self.log_text.insert(tk.END, "Déconnexion du serveur\n", "avertissement")
        self.destroy()


class IncomingCallWindow(tk.Toplevel):
    def __init__(self, c: Client, name):
        super().__init__(c.master)
        self.name = name
        self.c = c

        self.title(f"Incoming call from {name}")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.call_label = tk.Label(self, text=f"Incoming call from {name}")
        self.call_label.pack(side="top")

        self.accept_button = tk.Button(
            self, text="Accept", command=self.accept, bg="green"
        )
        self.accept_button.pack(side="right", anchor="s")

        self.decline_button = tk.Button(
            self, text="Decline", command=self.decline, bg="red"
        )
        self.decline_button.pack(side="left", anchor="s")

    def accept(self):
        self.c.accept_call(self.name)
        self.destroy()

    def decline(self):
        self.c.reject_call(self.name)
        self.destroy()


if __name__ == "__main__":
    client = Client()
    client.mainloop()
