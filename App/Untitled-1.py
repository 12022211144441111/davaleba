import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QGridLayout, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.start_btn_3 = QPushButton("First to 3")
        self.start_btn_5 = QPushButton("First to 5")
        self.start_label_1 = QLabel("Pick A Gamemode:")
        self.initStart()
        self.game_stats()

    def game_stats(self):
        self.ai_score = 0
        self.player_score = 0
        self.winner = None
    
    def initStart(self):
        self.setGeometry(300, 300, 600, 400)

        self.grid = QGridLayout()

        self.grid.addWidget(self.start_label_1, 0, 2)
        self.grid.addWidget(self.start_btn_3, 2, 1)
        self.grid.addWidget(self.start_btn_5, 2, 3)

        self.setLayout(self.grid)

        self.setStyleSheet("""
        QPushButton, QLabel {
            font-family: 'Comic Sans MS';
            font-weight: bold;
            font-size: 60px;
        }
        """)

        self.start_btn_3.clicked.connect(lambda: self.RefreshUI(3))
        self.start_btn_5.clicked.connect(lambda: self.RefreshUI(5))

    def RefreshUI(self, score):
        self.score_amount = score

        for widget in [self.start_btn_3, self.start_btn_5, self.start_label_1]:
            self.grid.removeWidget(widget)
            widget.deleteLater()

        old_layout = self.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        self.setGeometry(300, 300, 1200, 800)
        self.setWindowTitle("Rock Paper Scissors (by kurcxa)")

        self.initUI()

    def initUI(self):
        self.score = self.score_amount
        self.title = QLabel(f"Rock Paper Scissors (First to {self.score})")
        self.player_space = QLabel("Player (you):")
        self.player_move = QLabel("None")
        self.player_score_label = QLabel(f"Score: {self.player_score}")
        self.ai_score_label = QLabel(f"Score: {self.ai_score}")
        self.ai_space = QLabel("AI:")
        self.ai_move = QLabel("None")
        self.winner_label = QLabel("No Winner Yet")
        self.rock = QPushButton("🪨")
        self.scissors = QPushButton("✂️")
        self.paper = QPushButton("📄")
        self.nothing1 = QLabel()
        self.nothing2 = QLabel()
        self.nothing3 = QLabel()

        grid = QGridLayout()

        grid.addWidget(self.title, 0, 2)
        grid.addWidget(self.player_space, 1, 1)
        grid.addWidget(self.ai_space, 1, 3)
        grid.addWidget(self.player_move, 2, 1)
        grid.addWidget(self.ai_move, 2, 3)
        grid.addWidget(self.winner_label, 2, 2)
        grid.addWidget(self.nothing2, 3, 2)
        grid.addWidget(self.rock, 4, 1)
        grid.addWidget(self.paper, 4, 2)
        grid.addWidget(self.scissors, 4, 3)
        grid.addWidget(self.player_score_label, 3, 1)
        grid.addWidget(self.ai_score_label, 3, 3)


        self.setLayout(grid)

        self.rock.clicked.connect(lambda: self.player_choice("Rock"))
        self.paper.clicked.connect(lambda: self.player_choice("Paper"))
        self.scissors.clicked.connect(lambda: self.player_choice("Scissors"))

    def set_buttons_enabled(self, state: bool):
        self.rock.setEnabled(state)
        self.paper.setEnabled(state)
        self.scissors.setEnabled(state)

    def player_choice(self, choice):
        self.set_buttons_enabled(False)

        self.player_recieved = choice

        if choice == "Rock":
            self.player_move.setText("🪨")
        elif choice == "Paper":
            self.player_move.setText("📄")
        else:
            self.player_move.setText("✂️")

        self.ai_choice()

    def ai_choice(self):
        ai_choices = ["Rock", "Paper", "Scissors"]
        self.ai_recieved = random.choice(ai_choices)

        self.dots = 0
        self.increasing = True
        self.think_cycles = random.randint(6, 10)
        self.current_cycle = 0

        def animate():
            if self.current_cycle >= self.think_cycles:
                timer.stop()
                self.display_ai_result()
                return

            if self.increasing:
                self.dots += 1
                if self.dots == 3:
                    self.increasing = False
            else:
                self.dots -= 1
                if self.dots == 0:
                    self.increasing = True

            self.ai_move.setText("Thinking" + "." * self.dots)
            self.current_cycle += 1

        timer = QTimer(self)
        timer.timeout.connect(animate)
        timer.start(500)

    def display_ai_result(self):
        if self.ai_recieved == "Rock":
            self.ai_move.setText("🪨")
        elif self.ai_recieved == "Paper":
            self.ai_move.setText("📄")
        else:
            self.ai_move.setText("✂️")

        self.name_winner()

    def name_winner(self):
        player_decision = self.player_move.text()
        ai_decision = self.ai_move.text()

        if player_decision == ai_decision:
            self.winner_label.setText("It's a tie!")
            self.finish_round()
            return

        if (player_decision == "📄" and ai_decision == "🪨") or \
        (player_decision == "🪨" and ai_decision == "✂️") or \
        (player_decision == "✂️" and ai_decision == "📄"):
            
            self.winner_label.setText("Player Won!")
            self.player_score += 1
        else:
            self.winner_label.setText("AI Won!")
            self.ai_score += 1

        self.finish_round()

    def finish_round(self):
        self.player_score_label.setText(f"Score: {self.player_score}")
        self.ai_score_label.setText(f"Score: {self.ai_score}")

        self.set_buttons_enabled(True)

        if self.player_score >= self.score:
            self.winner_label.setText("🎉 PLAYER WINS THE GAME! 🎉")
            self.set_buttons_enabled(False)

        if self.ai_score >= self.score:
            self.winner_label.setText("🤖 AI WINS THE GAME! 🤖")
            self.set_buttons_enabled(False)

    def exit_app(self):
        QApplication.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = Main()
    game.show()
    sys.exit(app.exec_())
