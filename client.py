import socket
from threading import Thread
import os
from player import Player  # Import the Player class
from prettytable import PrettyTable  # Import PrettyTable for displaying stats

class Client:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))

        self.nickname = input("Enter your name: ")  # Prompt for player's name
        self.player = Player(self.nickname)  # Create a Player object
        
        # Send player's name to the server
        self.socket.send(self.nickname.encode())
        
        print(f"Connected to the server as {self.player.name}.")
        
        # Start listening for messages from the server
        Thread(target=self.receive_message, daemon=True).start()
        self.send_message()

    def send_message(self):
        """Handles sending messages to the server."""
        while True:
            try:
                message = input("")  # User input
                if message.lower() == "bye":
                    self.socket.send(message.encode())
                    print("Disconnected from server.")
                    self.socket.close()
                    os._exit(0)  # Exit the program
                elif message.lower().startswith("challenge"):
                    # Ensure the challenge message is valid
                    self.socket.send(message.encode())  # Send challenge message to server
                else:
                    self.socket.send(f"{self.player.name}: {message}".encode())  # Send player name with message
            except:
                break

    def receive_message(self):
        """Handles receiving messages from the server."""
        while True:
            try:
                message = self.socket.recv(1024).decode()
                if not message:
                    break
                print("\033[1;34;40m" + message + "\033[0m")  # Blue text
                
                # If the message contains player stats, display them
                try:
                    stats = eval(message)  # Convert string back to list of stats
                    self.display_player_stats(stats)  # Display the stats excluding the client's own
                except:
                    pass
            except:
                break

        print("Disconnected from server.")
        self.socket.close()
        os._exit(0)

    def display_player_stats(self, stats):
        """Display player stats in a table format excluding the client's own stats."""
        table = PrettyTable()

        # Set column headers
        table.field_names = ["#", "Name", "Games Played", "Games Won", "Win Ratio"]

        # Add rows with player stats, excluding the client's own data
        for idx, stat in enumerate(stats):
            if stat[0] != self.player.name:  # Exclude the current player's stats
                table.add_row([idx + 1] + stat)  # Add sequence number to the row

        # Print the table
        print("\nUpdated Player Stats (excluding yourself):")
        print(table)

# Start the client
Client('127.0.0.1', 7632)
