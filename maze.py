import random
from collections import deque

WIDTH = 51
HEIGHT = 31

# Higher = more open
OPENNESS = 0.20

# Terminal color for important objects
RED = "\033[91m"
RESET = "\033[0m"


def generate_maze():
    while True:
        maze = create_random_maze()

        if is_connected(maze):
            add_exit(maze)
            add_pacman(maze)
            return maze


def create_random_maze():
    # Start with an entirely open interior
    maze = [["." for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # Outer boundary
    for x in range(WIDTH):
        maze[0][x] = "#"
        maze[HEIGHT - 1][x] = "#"

    for y in range(HEIGHT):
        maze[y][0] = "#"
        maze[y][WIDTH - 1] = "#"

    # Add random walls
    for y in range(2, HEIGHT - 2, 2):
        for x in range(2, WIDTH - 2, 2):

            if random.random() > OPENNESS:

                directions = [
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1)
                ]

                dx, dy = random.choice(directions)

                nx = x + dx
                ny = y + dy

                if (
                    1 <= nx < WIDTH - 1
                    and 1 <= ny < HEIGHT - 1
                ):
                    maze[y][x] = "#"
                    maze[ny][nx] = "#"

    # Remove some walls to create loops
    for _ in range(int(WIDTH * HEIGHT * OPENNESS * 0.10)):

        x = random.randint(1, WIDTH - 2)
        y = random.randint(1, HEIGHT - 2)

        if maze[y][x] == "#":
            maze[y][x] = "."

    return maze


def is_connected(maze):
    """Check whether all walkable cells are connected."""

    start = None

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if maze[y][x] == ".":
                start = (x, y)
                break

        if start:
            break

    if start is None:
        return False

    queue = deque([start])
    visited = {start}

    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    while queue:

        x, y = queue.popleft()

        for dx, dy in directions:

            nx = x + dx
            ny = y + dy

            if (
                0 <= nx < WIDTH
                and 0 <= ny < HEIGHT
                and maze[ny][nx] == "."
                and (nx, ny) not in visited
            ):
                visited.add((nx, ny))
                queue.append((nx, ny))

    total_walkable = sum(
        row.count(".")
        for row in maze
    )

    return len(visited) == total_walkable


def add_exit(maze):
    """Place an exit on the outer boundary."""

    possible_exits = []

    # Top and bottom
    for x in range(1, WIDTH - 1):

        if maze[1][x] == ".":
            possible_exits.append((x, 0))

        if maze[HEIGHT - 2][x] == ".":
            possible_exits.append((x, HEIGHT - 1))

    # Left and right
    for y in range(1, HEIGHT - 1):

        if maze[y][1] == ".":
            possible_exits.append((0, y))

        if maze[y][WIDTH - 2] == ".":
            possible_exits.append((WIDTH - 1, y))

    exit_x, exit_y = random.choice(possible_exits)

    maze[exit_y][exit_x] = "E"


def add_pacman(maze):
    """Place Pac-Man on a random walkable cell."""

    possible_positions = []

    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):

            if maze[y][x] == ".":
                possible_positions.append((x, y))

    x, y = random.choice(possible_positions)

    maze[y][x] = "P"


def print_maze(maze):
    """Print the maze with important objects highlighted."""

    important_objects = {"P", "G", "o", "E"}

    for row in maze:

        for cell in row:

            if cell in important_objects:
                print(f"{RED}{cell}{RESET}", end="")
            else:
                print(cell, end="")

        print()


if __name__ == "__main__":

    maze = generate_maze()

    print_maze(maze)