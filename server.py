import socket
import threading
from player import Player  # Import the Player class
from prettytable import PrettyTable  # Import PrettyTable for displaying stats

class Server:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen()
        
        self.clients = []  # List of connected clients
        self.players = []  # List of Player objects

        print("Server waiting for connections...")

        self.accept_clients()

    def accept_clients(self):
        """Accept multiple clients and handle them in separate threads."""
        while True:
            client_socket, address = self.socket.accept()
            
            # Receive and store client's nickname
            nickname = client_socket.recv(1024).decode()
            player = Player(nickname)  # Create Player object for the client
            self.players.append(player)  # Add the player object to the list
            self.clients.append(client_socket)
            print(f"Connection from: {address} as {nickname}")

            # Send the updated player stats to all clients
            self.send_player_stats()

            # Start a new thread to handle the client
            threading.Thread(target=self.talk_to_client, args=(client_socket, player)).start()

    def talk_to_client(self, client_socket, player):
        """Handle communication with a specific client."""
        threading.Thread(target=self.receive_message, args=(client_socket, player)).start()

    def receive_message(self, client_socket, player):
        """Receive messages from a client and broadcast them."""
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message.strip():
                    break  # Empty message means the client disconnected

                print(f"{player.name}: {message}")  # Print message with player's name

                # Broadcast message to other clients
                self.broadcast(message, player.name, client_socket)
            except:
                break  # Handle client disconnection

        print(f"{player.name} disconnected.")
        self.clients.remove(client_socket)
        self.players.remove(player)
        client_socket.close()

        # Send the updated player stats after disconnection
        self.send_player_stats()

    def broadcast(self, message, nickname, sender_socket):
        """Send message to all clients except the sender."""
        for client, player in zip(self.clients, self.players):
            if client != sender_socket:
                try:
                    client.send(f"{nickname}: {message}".encode())
                except:
                    self.clients.remove(client)

    def send_player_stats(self):
        """Send the stats of all players (excluding themselves) to all clients."""
        stats = []
        for player in self.players:
            stats.append([player.name, player.games_played, player.games_won, round(player.win_ratio, 2)])

        # Send the player stats to all connected clients
        for client_socket in self.clients:
            try:
                client_socket.send(str(stats).encode())  # Send stats as a string
            except:
                pass

# Start the server
Server('127.0.0.1', 7632)
