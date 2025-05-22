# game.py

class RockPaperScissors:
    choices = ["rock", "paper", "scissors"]

    @staticmethod
    def determine_winner(choice1, choice2):
        """Determines the winner between two choices."""
        if choice1 == choice2:
            return "draw"
        elif (choice1 == "rock" and choice2 == "scissors") or \
             (choice1 == "scissors" and choice2 == "paper") or \
             (choice1 == "paper" and choice2 == "rock"):
            return "player1"
        else:
            return "player2"