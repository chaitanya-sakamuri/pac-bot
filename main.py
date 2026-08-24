import time

from maze import generate_maze
from world import World
from sensor import CardinalSensor
from brain import RuleBasedBrain
from mapper import Mapper


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
    mapper = Mapper()

    start_time = time.time()
    steps = 0

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
        # Update Pac-Bot's internal map
        exploration_reward, new_cells = mapper.update(
            vision,
            world.pacman_position
        )

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
        print("New area discovered:", new_cells)
        print("Exploration reward:", exploration_reward)
        


        # -------------------------
        # MOVE PAC-MAN
        # -------------------------

        if action is None:
            print("\nNo possible moves!")
            break

        success, reward, done = world.move_pacman(action)

        if success:
            steps += 1

        print("Reward:", reward)
        print("Ghost danger:", world.ghost_danger_reward())
        # -------------------------
        # MOVE GHOSTS
        # -------------------------

        world.move_ghosts()

        # -------------------------
        # CHECK GHOST COLLISION
        # -------------------------

        if world.check_ghost_collision():

            end_time = time.time()
            total_time = end_time - start_time

            clear_screen()

            print("========== PAC-BOT ==========\n")

            display_world(world)

            print()
            print("💀 PAC-MAN WAS CAUGHT BY A GHOST!")
            print("Reward: -100")
            print(f"Total time: {total_time:.2f} seconds")
            print(f"Total steps: {steps}")

            break

        # -------------------------
        # CHECK EXIT
        # -------------------------

        if done:

            clear_screen()

            print("========== PAC-BOT ==========\n")

            display_world(world)

            print()
            print("🚪 PAC-MAN REACHED THE EXIT!")
            print("Reward:", reward)
            end_time = time.time()
            total_time = end_time - start_time
            print(f"Total time: {total_time:.2f} seconds")
            print(f"Total steps: {steps}")

            break

        time.sleep(0.15)


if __name__ == "__main__":
    main()