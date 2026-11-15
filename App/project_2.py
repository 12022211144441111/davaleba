import random
import time

class Player:
    def __init__(self, name, plr_type):
        self.name = name
        self.plr_type = plr_type
        self.inventory = []
        self.set_player()
        self.max_health = self.health

    def set_player(self):
        if self.plr_type == "Warrior":
            self.health = 350
            self.inventory.append("Sword")
        elif self.plr_type == "Archer":
            self.health = 250
            self.inventory.append("Bow")

    def attack(self, other):
        self.set_damage()
        other.health -= self.damage

    def heal(self):
        self.set_healamount()
        self.health += self.healamount

    def set_damage(self):
        if "Sword" in self.inventory:
            if atk_range >= 5:
                self.damage = random.randint(15, 20)
            elif atk_range < 5:
                self.damage = random.randint(20, 25)

        if "Bow" in self.inventory:
            if atk_range >= 5:
                self.damage = random.randint(20, 25)
            elif atk_range < 5:
                self.damage = random.randint(15, 20)

    def set_healamount(self):
        if self.plr_type == "Warrior":
            self.healamount = random.randint(15, 20)
        elif self.plr_type == "Archer":
            self.healamount = random.randint(20, 25)

class Mob:
    def __init__(self, mob_type):
        self.mob_type = mob_type
        self.set_mob()

    def set_mob(self):
        if self.mob_type == "Goblin":
            self.health = 150
        elif self.mob_type == "Guard":
            self.health = 170
        elif self.mob_type == "Giant":
            self.health = 250
        elif self.mob_type == "Knight":
            self.health = 350

    def attack(self, other):
        self.set_damage()
        other.health -= self.damage

    def set_damage(self):
        if self.mob_type == "Goblin":
            self.damage = random.randint(15, 20)
        elif self.mob_type == "Guard":
            self.damage = random.randint(17, 22)
        elif self.mob_type == "Giant":
            self.damage = random.randint(16, 21)
        elif self.mob_type == "Knight":
            self.damage = random.randint(20, 24)

def create_player():
    name = input("💬 Enter your username: ")
    plr_type = input("🧐 Select class ((W)arrior ⚔️ , (A)rcher 🏹): ").upper()
    while plr_type not in ["W", "A"]:
        print("❗ Invalid class ❗")
        plr_type = input("> ").upper()

    print("✅ Player Created Successfully! ") 
    time.sleep(1)
    print("⏰ Starting Game! ") 
    time.sleep(0.5)

    return Player(name, "Warrior" if plr_type == "W" else "Archer")

def create_mob():
    return Mob(random.choice(["Goblin", "Guard", "Giant", "Knight"]))

def reward_plr(player, mob):
    num = random.randint(1, 3)
    if num == 1:
        print("🧪 You have found a Health Potion!")
        player.inventory.append("Health Potion")
    elif num == 2:
        print("💥 You have found a Damage Potion!")
        player.inventory.append("Damage Potion")
    else:
        print(f"😕 {mob.mob_type} had no items on him")


plr = create_player()
running = True
items = ["Health Potion", "Damage Potion"]
max_health = plr.max_health

while running:
    atk_range = random.randint(1, 10)
    print(f"\n↔ Attack Range - {atk_range}")
    time.sleep(random.randint(1, 3))
    mob = create_mob()
    print(f"\n⚠️ A wild {mob.mob_type} appears!")
    encountered = True

    while encountered:
        print(f"\n❤️ Your HP: {plr.health} | 👹 {mob.mob_type} HP: {mob.health}")
        print("1. Attack  2. Heal  3. Inventory  4. Run")

        while True:
            try:
                choice = int(input(">>> "))
                if choice in [1,2,3,4,5]:
                    break
                else:
                    print("❗ Invalid choice ❗")
            except ValueError:
                print("❗ Please enter a number ❗")

        if choice == 1:
            plr.attack(mob)
            print(f"⚔️ You attacked {mob.mob_type} for {plr.damage} HP!")
            if mob.health > 0:
                mob.attack(plr)
                print(f"❗ {mob.mob_type} attacked you for {mob.damage} HP!")

        elif choice == 2:
            plr.heal()
            plr.health = min(plr.health, max_health)
            print(f"❤️‍🩹 You have healed for {plr.healamount} HP!")
            if mob.health > 0:
                mob.attack(plr)
                print(f"❗ {mob.mob_type} attacked you for {mob.damage} HP!")

        elif choice == 3:
            print(f"Inventory: {plr.inventory}")
            print("1. Use Item  2. Exit Inventory")
            while True:
                try:
                    inv_choice = int(input(">>> "))
                    if inv_choice in [1,2]:
                        break
                    else:
                        print("❗ Invalid choice ❗")
                except ValueError:
                    print("❗ Please enter a number ❗")

            if inv_choice == 1:
                if not plr.inventory:
                    print("❌ Inventory is empty!")
                    continue
                for i, item in enumerate(plr.inventory):
                    print(f"{i+1}. {item}")
                while True:
                    try:
                        use_choice = int(input(">>> ")) - 1
                        if 0 <= use_choice < len(plr.inventory):
                            item = plr.inventory[use_choice]
                            break
                        else:
                            print("❗ Invalid selection ❗")
                    except ValueError:
                        print("❗ Please enter a number ❗")

                if item == "Health Potion":
                    plr.health = min(plr.health + 50, max_health)
                    print("✨ You used a Health Potion")
                    plr.inventory.pop(use_choice)
                elif item == "Damage Potion":
                    plr.attack(mob)
                    plr.attack(mob)
                    print(f"✨ You used a Damage Potion and attack {mob.mob_type} 2 times!")
                    plr.inventory.pop(use_choice)
                else:
                    print("❌ You can't use that item!")

        elif choice == 4:
            if random.randint(1, 3) == 1:
                print(f"🏃 You escaped from {mob.mob_type}!")
                encountered = False
            else:
                print("❌ Escape failed!")
                mob.attack(plr)
                print(f"❗ {mob.mob_type} hit you for {mob.damage} HP!")

        if plr.health <= 0:
            print("😞 You have died! Stopping Game!")
            running = False
            encountered = False
        elif mob.health <= 0:
            print(f"\n👑 You have won the battle against {mob.mob_type}!")
            reward_plr(plr, mob)
            encountered = False