# To Do List

def add_task(task):
    tasks.append(task)

def remove_task(task):
    tasks.remove(task)

def show_tasks():
    print(tasks)

tasks = []

running = True

while running:
    print("1.Show Tasks 2.Add Task 3.Remove Task 4.Exit App")
    choice = int(input("Select You Choice: "))
    
    while choice not in [1, 2, 3, 4]:
        print("Invalid Choice! Choose again!")
        choice = int(input("Select You Choice: "))

    if choice == 1:
        show_tasks()
    elif choice == 2:
        task = input("Enter Task: ")
        add_task(task)
    elif choice == 3:
        task = input("Enter Task: ")
        
        while task not in tasks:
            print("Invalid task")
            task = input("Enter Task: ")

        remove_task(task)
    elif choice == 4:
        running = False