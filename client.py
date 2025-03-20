from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QInputDialog, QListWidget
from PyQt5.QtCore import QThread, pyqtSignal
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
                        player_data = message.replace("Players:", "").strip()  # Remove "Players:" safely
                        player_list = list(set(p.strip() for p in player_data.split("\n") if p.strip()))  # Ensure unique names
                        self.client_gui.update_player_list(player_list)
                    else:
                        self.message_received.emit(message)
            except:
                break

    def stop(self):
        self.running = False
        self.quit()

class ClientGUI(QWidget):
    def __init__(self, host, port):
        super().__init__()
        self.setWindowTitle("Multiplayer Chat & Game")
        self.setGeometry(100, 100, 500, 600)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

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
        layout.addWidget(QLabel("Connected Players:"))
        layout.addWidget(self.player_list)
        
        self.setLayout(layout)

    def get_nickname(self):
        nickname, ok = QInputDialog.getText(self, "Enter Name", "Your Name:")
        if ok and nickname:
            self.nickname = nickname.strip()
            self.client_socket.send(self.nickname.encode())
        else:
            self.close()

    def display_message(self, message):
        if not message.startswith("Players:"):
            self.chat_display.append(message)

    def send_message(self):
        message = self.chat_input.text()
        if message:
            formatted_message = f"{self.nickname}: {message}"
            self.client_socket.send(formatted_message.encode())
            self.display_message(formatted_message)  # Show sent message to sender
            self.chat_input.clear()

    def update_player_list(self, player_names):
        self.player_list.clear()
        for player in sorted(player_names):  # Sorting to maintain consistent order
            if player and player != self.nickname:  # Exclude self from player list
                self.player_list.addItem(player)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ClientGUI("127.0.0.1", 7640)
    client.show()
    sys.exit(app.exec_())
