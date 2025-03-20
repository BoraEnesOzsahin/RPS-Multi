from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QLabel, QInputDialog, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMetaObject, Q_ARG, pyqtSlot
import socket
import sys

class ClientListener(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, client_socket, client_gui):
        super().__init__()
        self.client_socket = client_socket
        self.client_gui = client_gui
        self.running = True

    def run(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode(errors='ignore').strip()
                if message:
                    if message.startswith("Players:"):
                        player_data = message.replace("Players:", "").strip()
                        player_list = list(set(p.strip() for p in player_data.split("\n") if p.strip()))
                        self.client_gui.update_player_list(player_list)
                    elif message.startswith("Challenge Received"):
                        challenger = message.split(":")[1].strip()
                        print(f"DEBUG: Received challenge from {challenger}")  # Debugging log
                        # Ensure the UI updates correctly by forcing the pop-up to appear
                        QMetaObject.invokeMethod(self.client_gui, "show_rps_selection", Qt.QueuedConnection, Q_ARG(str, challenger))
                    elif message.startswith("Game Result"):
                        self.client_gui.display_message(message)
                    else:
                        self.message_received.emit(message)
            except Exception as e:
                print(f"Listener Error: {e}")
                break

    def stop(self):
        self.running = False
        self.quit()

class ClientGUI(QWidget):
    def __init__(self, host, port):
        super().__init__()
        self.setWindowTitle("Multiplayer Chat & Game")
        self.setGeometry(100, 100, 500, 700)

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
        except Exception as e:
            print(f"Connection Error: {e}")
            sys.exit()

        self.nickname = ""
        self.get_nickname()
        
        self.init_ui()
        
        self.listener = ClientListener(self.client_socket, self)
        self.listener.message_received.connect(self.display_message)
        self.listener.start()

    def init_ui(self):
        layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(QLabel("Chat:"))
        layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit()
        self.chat_input.returnPressed.connect(self.send_message)
        layout.addWidget(self.chat_input)

        self.player_list = QListWidget()
        layout.addWidget(QLabel("Connected Players & Stats:"))
        layout.addWidget(self.player_list)

        layout.addWidget(QLabel("Select Move Before Challenging:"))
        self.move_selector = QComboBox()
        self.move_selector.addItems(["Rock", "Paper", "Scissors"])
        layout.addWidget(self.move_selector)
        
        self.challenge_button = QPushButton("Challenge")
        self.challenge_button.clicked.connect(self.send_challenge)
        layout.addWidget(self.challenge_button)
        
        self.setLayout(layout)

    def get_nickname(self):
        nickname, ok = QInputDialog.getText(self, "Enter Name", "Your Name:")
        if ok and nickname:
            self.nickname = nickname.strip()
            self.client_socket.send(self.nickname.encode())
        else:
            print("No nickname provided. Exiting.")
            sys.exit()

    def display_message(self, message):
        if not message.startswith("Players:"):
            self.chat_display.append(message)

    def send_message(self):
        message = self.chat_input.text()
        if message:
            formatted_message = f"{self.nickname}: {message}"
            self.client_socket.send(message.encode())
            self.display_message(formatted_message)
            self.chat_input.clear()

    def update_player_list(self, player_names):
        self.player_list.clear()
        for player in sorted(player_names):
            if self.nickname not in player:
                self.player_list.addItem(player)

    def send_challenge(self):
        selected_player = self.player_list.currentItem()
        if selected_player:
            chosen_move = self.move_selector.currentText().lower()
            challenge_message = f"challenge {selected_player.text().split('-')[0].strip()} {chosen_move}"
            self.client_socket.send(challenge_message.encode())
            self.display_message(f"You challenged {selected_player.text().split('-')[0].strip()} with {chosen_move.capitalize()}!")
        else:
            self.display_message("Select a player to challenge!")

    @pyqtSlot(str)  # Ensures the function is recognized as a callable slot
    def show_rps_selection(self, challenger):
        """ Displays a selection box for the challenged player to choose their move. """
        print(f"DEBUG: Opening pop-up for challenge from {challenger}")  # Debugging log
        choice, ok = QInputDialog.getItem(self, "Rock-Paper-Scissors", 
                                          f"You've been challenged by {challenger}! Choose your move:", 
                                          ["Rock", "Paper", "Scissors"], 0, False)
        if ok and choice:
            print(f"DEBUG: {self.nickname} chose {choice}")  # Debugging log
            self.client_socket.send(f"choice {choice.lower()}".encode())
            self.display_message(f"You chose {choice}.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ClientGUI("127.0.0.1", 7640)
    client.show()
    sys.exit(app.exec_())
