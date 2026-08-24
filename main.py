import time

from maze import generate_maze
from world import World
from sensor import CardinalSensor
from brain import RuleBasedBrain


# --------------------------------------------------
# COLORS
# --------------------------------------------------

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


# --------------------------------------------------
# CLEAR TERMINAL
# --------------------------------------------------

def clear_screen():
    print("\033[2J\033[H", end="")


# --------------------------------------------------
# DISPLAY WORLD
# --------------------------------------------------

def display_world(world):

    display = [row[:] for row in world.maze]

    # Remove dynamic objects
    for y in range(len(display)):
        for x in range(len(display[y])):
            if display[y][x] in ("P", "G", "E"):
                display[y][x] = "."

    # Pellets
    for x, y in world.pellets:
        display[y][x] = f"{YELLOW}o{RESET}"

    # Ghosts
    for x, y in world.ghost_positions:
        if (x, y) != world.pacman_position:
            display[y][x] = f"{RED}G{RESET}"

    # Exit
    ex, ey = world.exit_position

    if (ex, ey) != world.pacman_position:
        display[ey][ex] = f"{GREEN}E{RESET}"

    # Pac-Man
    px, py = world.pacman_position
    display[py][px] = f"{RED}P{RESET}"

    for row in display:
        print("".join(row))


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    # Create ONE world
    maze = generate_maze()
    world = World(maze)

    # Create sensor
    sensor = CardinalSensor(world, max_range=8)

    # Create brain
    brain = RuleBasedBrain()

    while True:

        clear_screen()

        print("========== PAC-BOT ==========\n")

        display_world(world)

        print()
        print("Pac-Man position:", world.pacman_position)
        print("Pellets remaining:", len(world.pellets))

        # -------------------------
        # SENSOR
        # -------------------------

        vision = sensor.scan()

        print("\nPac-Man vision:")

        for direction, data in vision.items():
            print(f"{direction}: {data}")

        # -------------------------
        # BRAIN
        # -------------------------

        action = brain.choose_action(
            vision,
            world.pacman_position
        )

        print()
        print("Brain decision:", action)

        # -------------------------
        # MOVE
        # -------------------------

        if action is None:
            print("\nNo possible moves!")
            break

        world.move_pacman(action)

        # Move ghosts after Pac-Man moves
        world.move_ghosts()

        # Check collision
        if world.check_ghost_collision():

            clear_screen()

            print("========== PAC-BOT ==========\n")

            display_world(world)

            print()
            print("💀 PAC-MAN WAS CAUGHT BY A GHOST!")

            break

        time.sleep(0.15)


if __name__ == "__main__":
    main()