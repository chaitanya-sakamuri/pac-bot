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
        # Ghost AI memory
        self.ghost_last_known = [None] * self.num_ghosts

        # Ghosts move slower than Pac-Man
        self.ghost_tick = 0

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
    
    def ghost_danger_reward(self):
        """Return a penalty based on how close the nearest ghost is."""

        if not self.ghost_positions:
            return 0

        px, py = self.pacman_position

        # Find distance to nearest ghost
        distances = []

        for gx, gy in self.ghost_positions:
            distance = abs(px - gx) + abs(py - gy)
            distances.append(distance)

        nearest = min(distances)

        if nearest == 1:
            return -5.0

        elif nearest == 2:
            return -2.0

        elif nearest == 3:
            return -0.5

        return 0

    def move_pacman(self, direction):
        moves = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        if direction not in moves:
            return False, -0.1, False

        dx, dy = moves[direction]

        x, y = self.pacman_position

        new_x = x + dx
        new_y = y + dy

        # Can't move through walls or ghosts
        if not self.is_walkable(new_x, new_y):
            return False, -0.1, False

        # -------------------------
        # Base movement penalty
        # -------------------------

        reward = -0.1

        # Remove Pac-Man from old position
        self.maze[y][x] = "."

        # Move Pac-Man
        self.pacman_position = (new_x, new_y)


        # -------------------------
        # Ghost danger
        # -------------------------

        reward += self.ghost_danger_reward()
        # -------------------------
        # Collect pellet
        # -------------------------

        if (new_x, new_y) in self.pellets:
            self.pellets.remove((new_x, new_y))
            reward += 10

        # Mark Pac-Man's new position
        self.maze[new_y][new_x] = "P"

        # -------------------------
        # Reach exit
        # -------------------------

        if (new_x, new_y) == self.exit_position:
            reward += 100
            return True, reward, True

        return True, reward, False

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

    def ghost_can_see_pacman(self, ghost_position):
        """Check whether a ghost can directly see Pac-Man."""

        gx, gy = ghost_position
        px, py = self.pacman_position

        # Same row
        if gy == py:

            step = 1 if px > gx else -1

            for x in range(gx + step, px, step):

                if self.maze[gy][x] == "#":
                    return False

            return True

        # Same column
        if gx == px:

            step = 1 if py > gy else -1

            for y in range(gy + step, py, step):

                if self.maze[y][gx] == "#":
                    return False

            return True

        return False


    def move_ghost_toward(self, ghost_position, target, occupied):
        """Move a ghost one step toward a target."""

        gx, gy = ghost_position
        tx, ty = target

        possible_moves = []

        # Try directions that reduce distance to target first
        candidates = [
            (gx + (1 if tx > gx else -1), gy),
            (gx, gy + (1 if ty > gy else -1))
        ]

        # Add other directions as fallback
        candidates += [
            (gx + 1, gy),
            (gx - 1, gy),
            (gx, gy + 1),
            (gx, gy - 1)
        ]

        for new_x, new_y in candidates:

            # Outside maze
            if new_y < 0 or new_y >= len(self.maze):
                continue

            if new_x < 0 or new_x >= len(self.maze[0]):
                continue

            # Wall
            if self.maze[new_y][new_x] == "#":
                continue

            # Another ghost
            if (new_x, new_y) in occupied:
                continue

            return (new_x, new_y)

        return ghost_position


    def move_ghosts(self):
        """Move ghosts using limited vision and memory."""

        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1)
        ]

        # Ghosts move every second Pac-Man turn
        self.ghost_tick += 1

        if self.ghost_tick % 2 != 0:
            return

        new_positions = []

        for i, ghost_position in enumerate(self.ghost_positions):

            # -----------------------------------------
            # SEE PAC-MAN
            # -----------------------------------------

            if self.ghost_can_see_pacman(ghost_position):

                # Remember where Pac-Man was seen
                self.ghost_last_known[i] = self.pacman_position

            target = self.ghost_last_known[i]

            # -----------------------------------------
            # CHASE / SEARCH
            # -----------------------------------------

            if target is not None:

                new_position = self.move_ghost_toward(
                    ghost_position,
                    target,
                    new_positions
                )

                # Reached the last known position
                if new_position == target:

                    self.ghost_last_known[i] = None

            # -----------------------------------------
            # RANDOM WANDER
            # -----------------------------------------

            else:

                possible_moves = []

                gx, gy = ghost_position

                for dx, dy in directions:

                    new_x = gx + dx
                    new_y = gy + dy

                    # Outside maze
                    if new_y < 0 or new_y >= len(self.maze):
                        continue

                    if new_x < 0 or new_x >= len(self.maze[0]):
                        continue

                    # Wall
                    if self.maze[new_y][new_x] == "#":
                        continue

                    # Don't overlap another ghost
                    if (new_x, new_y) in new_positions:
                        continue

                    possible_moves.append((new_x, new_y))

                if possible_moves:
                    new_position = random.choice(possible_moves)
                else:
                    new_position = ghost_position

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