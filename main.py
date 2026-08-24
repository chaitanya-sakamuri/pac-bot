import sys
import termios
import tty

from maze import generate_maze
from world import World
from sensor import CardinalSensor


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

    # Copy the maze so the original maze is never changed
    display = [row[:] for row in world.maze]

    # Remove old dynamic objects from the copied maze
    # P, G and E should NOT permanently exist in the maze.
    for y in range(len(display)):
        for x in range(len(display[y])):
            if display[y][x] in ("P", "G", "E"):
                display[y][x] = "."

    # -------------------------
    # Draw pellets
    # -------------------------

    for x, y in world.pellets:
        display[y][x] = f"{YELLOW}o{RESET}"

    # -------------------------
    # Draw ghosts
    # -------------------------

    for x, y in world.ghost_positions:
        if (x, y) != world.pacman_position:
            display[y][x] = f"{RED}G{RESET}"

    # -------------------------
    # Draw exit
    # -------------------------

    ex, ey = world.exit_position

    if (ex, ey) != world.pacman_position:
        display[ey][ex] = f"{GREEN}E{RESET}"

    # -------------------------
    # Draw Pac-Man LAST
    # -------------------------

    px, py = world.pacman_position
    display[py][px] = f"{RED}P{RESET}"

    # Print maze
    for row in display:
        print("".join(row))


# --------------------------------------------------
# GET ONE KEY WITHOUT ENTER
# --------------------------------------------------

def get_key():

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(
            sys.stdin,
            termios.TCSADRAIN,
            old_settings
        )

    return key


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    # Generate ONE maze
    maze = generate_maze()

    # Create ONE world
    world = World(maze)

    # Sensor connected to THIS world
    sensor = CardinalSensor(world)

    while True:

        # Redraw the same screen
        clear_screen()

        print("========== PAC-BOT ==========\n")

        # Draw current world
        display_world(world)

        print()
        print("Pac-Man position:", world.pacman_position)
        print("Pellets remaining:", len(world.pellets))

        print()
        print("Pac-Man vision:")

        vision = sensor.scan()

        for direction, data in vision.items():
            print(f"{direction}: {data}")

        print()
        print("W/A/S/D = Move    Q = Quit")
        print("> ", end="", flush=True)

        # Read ONE key immediately
        command = get_key().lower()

        # Quit
        if command == "q":
            break

        # Keyboard → world direction
        directions = {
            "w": "UP",
            "s": "DOWN",
            "a": "LEFT",
            "d": "RIGHT"
        }

        if command in directions:

            direction = directions[command]

            # Move Pac-Man
            world.move_pacman(direction)


# --------------------------------------------------

if __name__ == "__main__":
    main()