from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QListWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import socket
import sys
import threading
from player import Player
from game import RockPaperScissors

class ServerListener(QThread):
    message_received = pyqtSignal(str, object)  # Now passes both message and sender socket

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
                    self.message_received.emit(message, self.client_socket)  # Pass both message and sender socket
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
        self.players = {}  # Dictionary to track Player objects
        self.challenges = {}  # Tracks ongoing challenges
        self.choices = {}  # Stores choices (rock, paper, scissors)

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
        layout.addWidget(QLabel("Connected Players & Stats:"))
        layout.addWidget(self.player_list)

        self.setLayout(layout)

    def accept_clients(self):
        while True:
            client_socket, address = self.server_socket.accept()
            nickname = client_socket.recv(1024).decode().strip()
            if client_socket not in self.players:
                self.players[client_socket] = Player(nickname)  # Create Player instance
                self.clients.append(client_socket)

            self.update_player_list()
            self.display_message(f"{nickname} has connected.")
            self.broadcast_player_list()

            listener = ServerListener(client_socket, self)
            listener.message_received.connect(self.handle_chat_message)  # Handle chat messages
            listener.start()

    def handle_chat_message(self, message, sender_socket):
        """Handles and displays chat messages in the server log with sender names."""
        sender_name = self.players[sender_socket].name if sender_socket in self.players else "Unknown"
        formatted_message = f"{sender_name}: {message}"
        self.display_message(formatted_message)  # Display formatted message in server log

    def display_message(self, message):
        """Displays messages in the server log."""
        self.chat_display.append(message)

    def update_player_list(self):
        self.player_list.clear()
        unique_players = sorted(set(f"{p.name} - Games: {p.games_played}, Wins: {p.games_won}, Win%: {p.win_ratio:.2f}" for p in self.players.values()))
        for player_info in unique_players:
            self.player_list.addItem(player_info)
        self.broadcast_player_list()

    def broadcast_player_list(self):
        unique_players = sorted(set(f"{p.name} - Games: {p.games_played}, Wins: {p.games_won}, Win%: {p.win_ratio:.2f}" for p in self.players.values()))
        player_list = "Players:\n" + "\n".join(unique_players)
        for client in self.clients:
            try:
                client.send(player_list.encode())
            except:
                self.remove_client(client)

    def handle_message(self, message, sender_socket):
        if message.startswith("challenge"):
            _, target_nickname, challenger_choice = message.split()
            target_socket = next((c for c, p in self.players.items() if p.name == target_nickname), None)

            if target_socket:
                self.challenges[sender_socket] = target_socket
                self.challenges[target_socket] = sender_socket
                self.choices[sender_socket] = challenger_choice  # Store challenger's move
                self.send_to_client(target_socket, f"Challenge Received: {self.players[sender_socket].name}")  # Send message

        elif message.startswith("choice"):
            self.choices[sender_socket] = message.split()[1]
            if sender_socket in self.challenges and self.challenges[sender_socket] in self.choices:
                self.determine_winner(sender_socket, self.challenges[sender_socket])

    def determine_winner(self, player1, player2):
        choice1 = self.choices[player1]
        choice2 = self.choices[player2]
        winner = RockPaperScissors.determine_winner(choice1, choice2)

        player1_name = self.players[player1].name
        player2_name = self.players[player2].name

        if winner == "draw":
            result_message = f"Game Result: It's a draw! {player1_name} chose {choice1}, {player2_name} chose {choice2}."
        elif winner == "player1":
            result_message = f"Game Result: {player1_name} wins! {player1_name} chose {choice1}, {player2_name} chose {choice2}."
            self.players[player1].add_game(won=True)
            self.players[player2].add_game(won=False)
        else:
            result_message = f"Game Result: {player2_name} wins! {player1_name} chose {choice1}, {player2_name} chose {choice2}."
            self.players[player1].add_game(won=False)
            self.players[player2].add_game(won=True)

        self.send_to_client(player1, result_message)
        self.send_to_client(player2, result_message)

        del self.challenges[player1], self.challenges[player2]
        del self.choices[player1], self.choices[player2]

        self.update_player_list()  # Update stats after the game

    def send_to_client(self, client, message):
        try:
            client.send(message.encode())
        except:
            self.remove_client(client)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            nickname = self.players[client_socket].name if client_socket in self.players else "Unknown"
            self.clients.remove(client_socket)
            del self.players[client_socket]
            self.update_player_list()
            client_socket.close()
            self.display_message(f"{nickname} has disconnected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = ServerGUI("127.0.0.1", 7640)
    server.show()
    sys.exit(app.exec_())
