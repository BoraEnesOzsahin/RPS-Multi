from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QListWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import socket
import sys
import threading

class ServerListener(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, client_socket, server):
        super().__init__()
        self.client_socket = client_socket
        self.server = server
        self.running = True

    def run(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode().strip()
                if message:
                    self.message_received.emit(message)
                    self.server.handle_message(message, self.client_socket)
            except:
                break

    def stop(self):
        self.running = False
        self.quit()

class ServerGUI(QWidget):
    def __init__(self, host, port):
        super().__init__()
        self.setWindowTitle("Multiplayer Server")
        self.setGeometry(100, 100, 500, 600)
        self.clients = []
        self.nicknames = {}
        self.challenges = {}
        self.choices = {}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        self.init_ui()

        threading.Thread(target=self.accept_clients, daemon=True).start()

    def init_ui(self):
        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(QLabel("Server Log:"))
        layout.addWidget(self.chat_display)

        self.player_list = QListWidget()
        layout.addWidget(QLabel("Connected Players:"))
        layout.addWidget(self.player_list)

        self.setLayout(layout)

    def accept_clients(self):
        while True:
            client_socket, address = self.server_socket.accept()
            nickname = client_socket.recv(1024).decode().strip()
            if client_socket not in self.nicknames:
                self.nicknames[client_socket] = nickname
                self.clients.append(client_socket)

            self.update_player_list()
            self.display_message(f"{nickname} has connected.")
            self.broadcast_player_list()

            listener = ServerListener(client_socket, self)
            listener.message_received.connect(self.display_message)
            listener.start()

    def display_message(self, message):
        self.chat_display.append(message)

    def update_player_list(self):
        self.player_list.clear()
        unique_players = sorted(set(self.nicknames.values()))  # Ensure uniqueness
        for nickname in unique_players:
            self.player_list.addItem(nickname)
        self.broadcast_player_list()

    def broadcast_player_list(self):
        unique_players = sorted(set(self.nicknames.values()))  # Avoid duplicates
        player_list = "Players:\n" + "\n".join(unique_players)
        for client in self.clients:
            try:
                client.send(player_list.encode())
            except:
                self.remove_client(client)

    def handle_message(self, message, sender_socket):
        self.broadcast(message, sender_socket)

    def broadcast(self, message, sender_socket):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode())
                except:
                    self.remove_client(client)
    
    def remove_client(self, client_socket):
        if client_socket in self.clients:
            nickname = self.nicknames.get(client_socket, "Unknown")
            self.clients.remove(client_socket)
            del self.nicknames[client_socket]
            self.update_player_list()
            client_socket.close()
            self.display_message(f"{nickname} has disconnected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = ServerGUI("127.0.0.1", 7640)
    server.show()
    sys.exit(app.exec_())
