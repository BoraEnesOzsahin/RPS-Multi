import socket
from threading import Thread
from player import Player

class Server:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen()

        self.clients = {}  # Store client sockets mapped to player objects
        print("Server waiting for connections...")

        # Accept multiple clients
        self.accept_clients()

    def accept_clients(self):
        """Accept new clients and start a thread for each."""
        while True:
            client_socket, address = self.socket.accept()
            print(f"Connection from: {address}")

            # Get the player's name from the client
            client_socket.send("Enter your name: ".encode())
            player_name = client_socket.recv(1024).decode().strip()

            if not player_name:
                client_socket.close()
                continue

            # Create Player object
            player = Player(player_name)
            
            # Store the client and associated player
            self.clients[client_socket] = player

            print(f"{player_name} has joined.")
            self.send_player_stats()

            # Start a new thread for the client
            Thread(target=self.handle_client, args=(client_socket, player), daemon=True).start()

    def handle_client(self, client_socket, player):
        """Handle communication with a client."""
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message.strip():
                    break  # Client disconnected

                print(f"{player.name}: {message}")

                if message.lower().startswith("challenge"):
                    self.handle_challenge(client_socket, message, player)
                else:
                    self.broadcast(message, player.name, client_socket)

            except Exception as e:
                print(f"Error: {e}")
                break

        # Remove disconnected client
        print(f"{player.name} disconnected.")
        del self.clients[client_socket]
        client_socket.close()

        # Update player stats for remaining clients
        self.send_player_stats()

    def send_player_stats(self):
        """Send player stats to all clients."""
        stats = [[p.name, p.games_played, p.games_won, p.win_ratio] for p in self.clients.values()]

        for client_socket in self.clients:
            filtered_stats = [stat for stat in stats if stat[0] != self.clients[client_socket].name]  # Exclude self
            client_socket.send(str(filtered_stats).encode())

    def handle_challenge(self, client_socket, message, player):
        """Handle player challenge requests."""
        parts = message.split()
        if len(parts) != 2 or not parts[1].isdigit():
            client_socket.send("Invalid challenge format. Use: challenge <number>\n".encode())
            return

        target_index = int(parts[1]) - 1  # Convert to zero-based index
        players_list = list(self.clients.values())

        if target_index < 0 or target_index >= len(players_list):
            client_socket.send("Invalid player number.\n".encode())
            return

        target_player = players_list[target_index]

        if target_player.name == player.name:
            client_socket.send("You cannot challenge yourself!\n".encode())
            return

        # Notify both players about the challenge
        for sock, p in self.clients.items():
            if p == target_player:
                sock.send(f"You have been challenged by {player.name}!\n".encode())
                client_socket.send(f"You have challenged {target_player.name}!\n".encode())
                return


# Start the server
Server('127.0.0.1', 7632)
