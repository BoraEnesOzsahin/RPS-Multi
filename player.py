class Player:
    def __init__(self, name):
        self.name = name
        self.games_played = 0
        self.games_won = 0
        self.win_ratio = 0.0

    def add_game(self, won=False):
        self.games_played += 1
        if won:
            self.games_won += 1
        self._update_win_ratio()

    def _update_win_ratio(self):
        if self.games_played > 0:
            self.win_ratio = self.games_won / self.games_played
        else:
            self.win_ratio = 0.0