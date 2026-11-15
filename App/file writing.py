import string
import random
from time import sleep

MAP_SIZE = 5
DIRECTIONS = ["north", "south", "east", "west"]
ROOM_EVENTS = ["enemy", "treasure", "trap", "empty"]
ENEMIES = ["Goblin", "Skeleton", "Dark Wolf"]
SPELLS = ["fireball", "heal"]

player = {
    "health": 100,
    "max_health": 100,
    "level": 1,
    "xp": 0,
    "gold": 0,
    "potions": 1,
    "spells": ["fireball"],
    "position": [0, 0],
    "alive": True,
    "visited": set()
}

game_map = {}
for x in range(MAP_SIZE):
    for y in range(MAP_SIZE):
        game_map[(x, y)] = random.choice(ROOM_EVENTS)

EXIT_POSITION = (MAP_SIZE - 1, MAP_SIZE - 1)
game_map[EXIT_POSITION] = "boss"

def slow_print(text, delay=0.02):
    for c in text:
        print(c, end="", flush=True)
        sleep(delay)
    print()

def sanitize(text):
    return text.lower().strip().translate(
        str.maketrans("", "", string.punctuation)
    )

def show_stats():
    slow_print(
        f"❤️ {player['health']}/{player['max_health']} "
        f"| 🧠 Lvl {player['level']} ({player['xp']} XP) "
        f"| 💰 {player['gold']}g "
        f"| 🧪 {player['potions']}"
    )

def level_up():
    while player["xp"] >= player["level"] * 50:
        player["xp"] -= player["level"] * 50
        player["level"] += 1
        player["max_health"] += 20
        player["health"] = player["max_health"]
        slow_print(f"⬆️ You leveled up! Level {player['level']}!")

        if player["level"] == 2:
            player["spells"].append("heal")
            slow_print("✨ You learned the spell: HEAL")

def move_player(direction):
    x, y = player["position"]

    if direction == "north": y += 1
    if direction == "south": y -= 1
    if direction == "east":  x += 1
    if direction == "west":  x -= 1

    if 0 <= x < MAP_SIZE and 0 <= y < MAP_SIZE:
        player["position"] = [x, y]
        return True
    slow_print("🚫 You can't go that way.")
    return False

def show_map():
    slow_print("\n🗺️ Dungeon Map:")
    for y in reversed(range(MAP_SIZE)):
        row = ""
        for x in range(MAP_SIZE):
            pos = (x, y)
            if pos == tuple(player["position"]):
                row += " P "
            elif pos in player["visited"]:
                row += " . "
            else:
                row += " ? "
        print(row)
    print()

def enemy_event():
    enemy = random.choice(ENEMIES)
    enemy_hp = random.randint(25, 45)

    slow_print(f"⚔️ A {enemy} attacks!")

    while enemy_hp > 0 and player["health"] > 0:
        slow_print("(attack / spell / run)")
        choice = sanitize(input("> "))

        if choice == "attack":
            dmg = random.randint(10, 20) + player["level"] * 2
            enemy_hp -= dmg
            slow_print(f"You deal {dmg} damage!")

        elif choice == "spell" and player["spells"]:
            slow_print(f"Spells: {', '.join(player['spells'])}")
            spell = sanitize(input("> "))
            if spell == "fireball":
                dmg = random.randint(20, 35)
                enemy_hp -= dmg
                slow_print(f"🔥 Fireball hits for {dmg}!")
            elif spell == "heal":
                heal = random.randint(20, 30)
                player["health"] = min(player["max_health"], player["health"] + heal)
                slow_print(f"✨ You heal {heal} HP!")
            else:
                slow_print("Spell failed!")

        elif choice == "run":
            if random.random() < 0.5:
                slow_print("🏃 You escaped!")
                return
            slow_print("❌ Escape failed!")

        if enemy_hp > 0:
            enemy_dmg = random.randint(5, 15)
            player["health"] -= enemy_dmg
            slow_print(f"The {enemy} hits for {enemy_dmg}!")

    if player["health"] <= 0:
        player["alive"] = False
        slow_print("💀 You were slain.")
    else:
        xp = random.randint(20, 35)
        gold = random.randint(10, 30)
        player["xp"] += xp
        player["gold"] += gold
        slow_print(f"🏆 Victory! +{xp} XP, +{gold} gold")
        level_up()

def boss_event():
    slow_print("👑 THE DUNGEON LORD APPEARS 👑")
    boss_hp = 120

    while boss_hp > 0 and player["health"] > 0:
        slow_print("(attack / spell)")
        choice = sanitize(input("> "))

        if choice == "attack":
            dmg = random.randint(15, 25) + player["level"] * 3
            boss_hp -= dmg
            slow_print(f"You strike for {dmg}!")

        elif choice == "spell":
            if "fireball" in player["spells"]:
                dmg = random.randint(30, 45)
                boss_hp -= dmg
                slow_print(f"🔥 Massive fireball! {dmg} damage!")

        if boss_hp > 0:
            dmg = random.randint(15, 25)
            player["health"] -= dmg
            slow_print(f"💥 Boss hits you for {dmg}!")

    if player["health"] > 0:
        slow_print("🎉 YOU DEFEATED THE BOSS!")
        slow_print("🚪 You escape victorious!")
    else:
        slow_print("💀 The boss crushes you...")

    player["alive"] = False

def treasure_event():
    if random.random() < 0.5:
        gold = random.randint(20, 50)
        player["gold"] += gold
        slow_print(f"💰 Found {gold} gold!")
    else:
        player["potions"] += 1
        slow_print("🧪 Found a potion!")

def trap_event():
    dmg = random.randint(10, 25)
    player["health"] -= dmg
    slow_print(f"☠️ Trap! You take {dmg} damage.")
    if player["health"] <= 0:
        player["alive"] = False

def empty_event():
    slow_print("The room is quiet...")

def process_room():
    pos = tuple(player["position"])
    player["visited"].add(pos)
    event = game_map[pos]
    game_map[pos] = "empty"

    if event == "enemy": enemy_event()
    elif event == "treasure": treasure_event()
    elif event == "trap": trap_event()
    elif event == "boss": boss_event()
    else: empty_event()

slow_print("🏰 DUNGEON ADVENTURE: DELUXE EDITION")
slow_print("Survive. Level up. Defeat the boss.\n")

process_room()

while player["alive"]:
    show_stats()
    show_map()
    slow_print("(north/south/east/west/map/inventory/quit)")
    cmd = sanitize(input("> "))

    if cmd in DIRECTIONS:
        if move_player(cmd):
            process_room()
    elif cmd == "inventory":
        slow_print(f"🧪 Potions: {player['potions']}")
        if player["potions"] > 0:
            slow_print("Use potion? (yes/no)")
            if sanitize(input("> ")) == "yes":
                player["potions"] -= 1
                heal = random.randint(25, 40)
                player["health"] = min(player["max_health"], player["health"] + heal)
                slow_print(f"✨ Healed {heal} HP!")
    elif cmd == "map":
        show_map()
    elif cmd == "quit":
        break
    else:
        slow_print("❓ Unknown command.")

slow_print("\n🛑 GAME OVER")
slow_print(f"Final Level: {player['level']}")
slow_print(f"Gold Collected: {player['gold']}")
slow_print(f"Rooms Explored: {len(player['visited'])}")