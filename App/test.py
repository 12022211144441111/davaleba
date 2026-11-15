import random

choices = ("Rock", "Papper", "Scissors")

while True:
    print("Welcome to rock paper scissors!")
    plr_choice = input("Enter your choice >>> ")
    ai_choice = random.choice(choices)

    while plr_choice not in ["Rock", "Paper", "Scissors"]:
        print("Invalid Choice!")
        plr_choice = input(">>> ")

    if plr_choice == "Rock" and ai_choice == "Scissors":
        print("You have won!")
        continue
    elif plr_choice == "Scissors" and ai_choice == "Paper":
        print("You have won!")
        continue
    elif plr_choice == "Paper" and ai_choice == "Rock":
        print("You have won!")
        continue
    elif plr_choice == ai_choice:
        print("It's a tie!")
        continue
    else:
        print("You lost!")
        continue