import random


class World:

    def __init__(self, maze):
        self.maze = maze

        # Find Pac-Man and exit
        self.pacman_position = self.find_object("P")
        self.exit_position = self.find_object("E")

        # Game objects
        self.ghost_positions = []
        self.pellets = set()

        # Number of objects
        self.num_ghosts = 3
        self.num_pellets = 30

        # Spawn them
        self.add_ghosts()
        self.add_pellets()

    def find_object(self, symbol):
        """Find the position of an object in the maze."""

        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):

                if cell == symbol:
                    return (x, y)

        return None

    def get_empty_positions(self):
        """Return all walkable cells that are currently empty."""

        positions = []

        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):

                if cell == ".":
                    positions.append((x, y))

        return positions

    def add_ghosts(self):
        """Place ghosts randomly on empty walkable cells."""

        available = self.get_empty_positions()

        for _ in range(self.num_ghosts):

            if not available:
                break

            position = random.choice(available)

            self.ghost_positions.append(position)

            available.remove(position)

            x, y = position
            self.maze[y][x] = "G"

    def add_pellets(self):
        """Place pellets randomly on remaining empty cells."""

        available = self.get_empty_positions()

        # Don't place more pellets than available cells
        amount = min(self.num_pellets, len(available))

        selected = random.sample(available, amount)

        for position in selected:

            self.pellets.add(position)

            x, y = position
            self.maze[y][x] = "o"

    def is_walkable(self, x, y):
        """Check whether Pac-Man can move to a cell."""

        # Outside maze
        if y < 0 or y >= len(self.maze):
            return False

        if x < 0 or x >= len(self.maze[0]):
            return False

        # Wall
        if self.maze[y][x] == "#":
            return False

        # Ghost
        if (x, y) in self.ghost_positions:
            return False

        return True

    def move_pacman(self, direction):
        moves = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        if direction not in moves:
            return False

        dx, dy = moves[direction]

        x, y = self.pacman_position

        new_x = x + dx
        new_y = y + dy

        # Can't move through walls or ghosts
        if not self.is_walkable(new_x, new_y):
            return False

        # Remove Pac-Man from old position
        self.maze[y][x] = "."

        # Move Pac-Man
        self.pacman_position = (new_x, new_y)

        # Collect pellet
        if (new_x, new_y) in self.pellets:
            self.pellets.remove((new_x, new_y))

        # Mark Pac-Man's new position
        self.maze[new_y][new_x] = "P"

        return True

    def get_neighbors(self):
        """Return all directions Pac-Man can currently move."""

        x, y = self.pacman_position

        directions = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        neighbors = {}

        for direction, (dx, dy) in directions.items():

            new_x = x + dx
            new_y = y + dy

            if self.is_walkable(new_x, new_y):
                neighbors[direction] = (new_x, new_y)

        return neighbors

    def move_ghosts(self):
        """Move all ghosts randomly."""

        directions = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        new_positions = []

        for ghost_x, ghost_y in self.ghost_positions:

            possible_moves = []

            for dx, dy in directions.values():

                new_x = ghost_x + dx
                new_y = ghost_y + dy

                # Outside maze
                if new_y < 0 or new_y >= len(self.maze):
                    continue

                if new_x < 0 or new_x >= len(self.maze[0]):
                    continue

                # Wall
                if self.maze[new_y][new_x] == "#":
                    continue

                # Don't move onto another ghost
                if (new_x, new_y) in new_positions:
                    continue

                possible_moves.append((new_x, new_y))

            # Move randomly if possible
            if possible_moves:
                new_position = random.choice(possible_moves)
            else:
                new_position = (ghost_x, ghost_y)

            new_positions.append(new_position)

        self.ghost_positions = new_positions

    def check_ghost_collision(self):
        """Check whether Pac-Man is touching a ghost."""

        return self.pacman_position in self.ghost_positions
        


# --------------------------------------------------
# TESTING
# --------------------------------------------------

if __name__ == "__main__":

    from maze import generate_maze, print_maze

    maze = generate_maze()

    world = World(maze)

    print("Initial world:")
    print_maze(world.maze)

    print()

    print("Pac-Man position:", world.pacman_position)
    print("Exit position:", world.exit_position)

    print("Ghost positions:", world.ghost_positions)

    print("Pellets:", len(world.pellets))

    print()

    print("Available moves:")

    for direction, position in world.get_neighbors().items():
        print(f"{direction}: {position}")