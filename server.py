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
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
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
            nickname = client_socket.recv(1024).decode()
            self.nicknames[client_socket] = nickname
            self.clients.append(client_socket)

            self.update_player_list()
            self.display_message(f"{nickname} has connected.")

            listener = ServerListener(client_socket, self)
            listener.message_received.connect(self.display_message)
            listener.start()

    def display_message(self, message):
        self.chat_display.append(message)

    def update_player_list(self):
        self.player_list.clear()
        for nickname in self.nicknames.values():
            self.player_list.addItem(nickname)

    def handle_message(self, message, sender_socket):
        if message.startswith("challenge"):
            challenger_nickname = self.nicknames[sender_socket]
            target_nickname = message.split()[1]
            target_socket = next((c for c, n in self.nicknames.items() if n == target_nickname), None)
            
            if target_socket:
                self.challenges[sender_socket] = target_socket
                self.challenges[target_socket] = sender_socket
                self.send_to_client(sender_socket, f"Challenge sent to {target_nickname}!")
                self.send_to_client(target_socket, f"You have been challenged by {challenger_nickname}. Choose Rock, Paper, or Scissors.")
            else:
                self.send_to_client(sender_socket, f"Player {target_nickname} not found!")

        elif message in ["rock", "paper", "scissors"]:
            self.choices[sender_socket] = message
            if sender_socket in self.challenges and self.challenges[sender_socket] in self.choices:
                self.determine_winner(sender_socket, self.challenges[sender_socket])
        else:
            self.broadcast(message, sender_socket)

    def determine_winner(self, player1, player2):
        choice1, choice2 = self.choices[player1], self.choices[player2]
        result = "It's a draw!" if choice1 == choice2 else (
            f"{self.nicknames[player1]} wins!" if (choice1, choice2) in [("rock", "scissors"), ("scissors", "paper"), ("paper", "rock")] else f"{self.nicknames[player2]} wins!"
        )

        self.send_to_client(player1, result)
        self.send_to_client(player2, result)

        del self.challenges[player1], self.challenges[player2], self.choices[player1], self.choices[player2]

    def send_to_client(self, client, message):
        client.send(message.encode())

    def broadcast(self, message, sender_socket):
        for client in self.clients:
            if client != sender_socket:
                client.send(message.encode())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = ServerGUI("127.0.0.1", 7640)
    server.show()
    sys.exit(app.exec_())
