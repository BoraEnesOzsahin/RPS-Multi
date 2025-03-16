import socket
from threading import Thread
import os
from player import Player  # Import the Player class

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
            except:
                break

        print("Disconnected from server.")
        self.socket.close()
        os._exit(0)

# Start the client
Client('127.0.0.1', 7632)
