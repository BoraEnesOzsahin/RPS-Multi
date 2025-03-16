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

            # Print the updated player stats in a table
            self.display_player_stats()

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

        # Print the updated player stats in a table after disconnection
        self.display_player_stats()

    def broadcast(self, message, nickname, sender_socket):
        """Send message to all clients except the sender."""
        for client, player in zip(self.clients, self.players):
            if client != sender_socket:
                try:
                    client.send(f"{nickname}: {message}".encode())
                except:
                    self.clients.remove(client)

    def display_player_stats(self):
        """Displays the stats of all players in a table."""
        table = PrettyTable()

        # Set column headers
        table.field_names = ["Name", "Games Played", "Games Won", "Win Ratio"]

        # Add rows with player stats
        for player in self.players:
            table.add_row([player.name, player.games_played, player.games_won, round(player.win_ratio, 2)])

        # Print the table
        print("\nPlayer Stats:")
        print(table)

# Start the server
Server('127.0.0.1', 7632)
