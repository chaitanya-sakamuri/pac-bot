import random


class World:

    def __init__(self, maze):

        # ==================================================
        # STATIC MAZE
        # ==================================================

        # Make a clean copy so dynamic objects such as
        # Pac-Man and ghosts never become part of the
        # underlying maze representation.
        self.maze = [
            row[:]
            for row in maze
        ]

        # ==================================================
        # STATIC OBJECTS
        # ==================================================

        self.pacman_position = (
            self.find_object("P")
        )

        self.exit_position = (
            self.find_object("E")
        )

        # ==================================================
        # DYNAMIC OBJECTS
        # ==================================================

        self.ghost_positions = []

        self.pellets = set()

        # ==================================================
        # SETTINGS
        # ==================================================

        self.num_ghosts = 3
        self.num_pellets = 30

        # Each ghost remembers the last position where
        # it saw Pac-Man.
        self.ghost_last_known = (
            [None] * self.num_ghosts
        )

        # Ghost cadence is deterministic: three moves per four decision ticks.
        self.ghost_tick = 0

        # ==================================================
        # INITIALIZE WORLD
        # ==================================================

        self._remove_dynamic_symbols()

        self.add_ghosts()
        self.add_pellets()

    # ==================================================
    # FIND OBJECT
    # ==================================================

    def find_object(
        self,
        symbol
    ):

        for y, row in enumerate(
            self.maze
        ):

            for x, cell in enumerate(
                row
            ):

                if cell == symbol:

                    return (
                        x,
                        y
                    )

        return None

    # ==================================================
    # REMOVE DYNAMIC SYMBOLS
    # ==================================================

    def _remove_dynamic_symbols(self):

        """
        Convert the original maze into a static maze.

        P and dynamic G/o symbols are removed.

        The exit E is preserved.
        """

        for y in range(
            len(self.maze)
        ):

            for x in range(
                len(self.maze[y])
            ):

                cell = self.maze[y][x]

                if cell in (
                    "P",
                    "G",
                    "o"
                ):

                    self.maze[y][x] = "."

    # ==================================================
    # EMPTY POSITIONS
    # ==================================================

    def get_empty_positions(self):

        """
        Return all currently available walkable cells.

        These are cells in the static maze that are not
        walls and are not occupied by a dynamic object.
        """

        positions = []

        for y, row in enumerate(
            self.maze
        ):

            for x, cell in enumerate(
                row
            ):

                if cell == "#":
                    continue

                if (
                    x,
                    y
                ) == self.pacman_position:
                    continue

                if (
                    x,
                    y
                ) == self.exit_position:
                    continue

                if (
                    x,
                    y
                ) in self.ghost_positions:
                    continue

                if (
                    x,
                    y
                ) in self.pellets:
                    continue

                positions.append(
                    (
                        x,
                        y
                    )
                )

        return positions

    # ==================================================
    # ADD GHOSTS
    # ==================================================

    def add_ghosts(self):

        available = (
            self.get_empty_positions()
        )

        for _ in range(
            self.num_ghosts
        ):

            if not available:
                break

            position = random.choice(
                available
            )

            self.ghost_positions.append(
                position
            )

            available.remove(
                position
            )

    # ==================================================
    # ADD PELLETS
    # ==================================================

    def add_pellets(self):

        available = (
            self.get_empty_positions()
        )

        amount = min(
            self.num_pellets,
            len(available)
        )

        selected = random.sample(
            available,
            amount
        )

        for position in selected:

            self.pellets.add(
                position
            )

    # ==================================================
    # IS WALKABLE
    # ==================================================

    def is_walkable(
        self,
        x,
        y,
        ignore_ghosts=False
    ):

        # --------------------------------------------------
        # OUTSIDE
        # --------------------------------------------------

        if (
            y < 0
            or y >= len(self.maze)
        ):

            return False

        if (
            x < 0
            or x >= len(self.maze[0])
        ):

            return False

        # --------------------------------------------------
        # WALL
        # --------------------------------------------------

        if self.maze[y][x] == "#":

            return False

        # --------------------------------------------------
        # GHOST
        # --------------------------------------------------

        if (
            not ignore_ghosts
            and (
                x,
                y
            ) in self.ghost_positions
        ):

            return False

        return True

    def get_pacman_valid_actions(self):
        """Return the single authoritative legal-action mask for Pac-Man.

        A legal move must remain in bounds, avoid a wall, and avoid a cell
        currently occupied by a ghost.  Decision code should use this instead
        of inferring legality from sensor data alone.
        """

        directions = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        x, y = self.pacman_position

        return [
            direction
            for direction, (dx, dy) in directions.items()
            if self.is_walkable(x + dx, y + dy)
        ]

    # ==================================================
    # GHOST DANGER
    # ==================================================

    def ghost_danger_reward(self):

        if not self.ghost_positions:

            return 0

        px, py = (
            self.pacman_position
        )

        distances = []

        for gx, gy in (
            self.ghost_positions
        ):

            distance = (
                abs(px - gx)
                + abs(py - gy)
            )

            distances.append(
                distance
            )

        nearest = min(
            distances
        )

        if nearest == 1:

            return -5.0

        elif nearest == 2:

            return -2.0

        elif nearest == 3:

            return -0.5

        return 0

    # ==================================================
    # MOVE PAC-MAN
    # ==================================================

    def move_pacman(
        self,
        direction
    ):

        moves = {

            "UP": (
                0,
                -1
            ),

            "DOWN": (
                0,
                1
            ),

            "LEFT": (
                -1,
                0
            ),

            "RIGHT": (
                1,
                0
            )
        }

        if direction not in moves:

            return (
                False,
                -0.1,
                False
            )

        dx, dy = moves[
            direction
        ]

        x, y = (
            self.pacman_position
        )

        new_x = (
            x + dx
        )

        new_y = (
            y + dy
        )

        # ==================================================
        # MOVEMENT VALIDATION
        # ==================================================

        if not self.is_walkable(
            new_x,
            new_y
        ):

            return (
                False,
                -0.1,
                False
            )

        # ==================================================
        # BASE REWARD
        # ==================================================

        reward = -0.05

        # ==================================================
        # MOVE
        # ==================================================

        self.pacman_position = (
            new_x,
            new_y
        )

        # ==================================================
        # GHOST DANGER
        # ==================================================

        reward += (
            self.ghost_danger_reward()
        )

        # ==================================================
        # PELLET
        # ==================================================

        if (
            new_x,
            new_y
        ) in self.pellets:

            self.pellets.remove(
                (
                    new_x,
                    new_y
                )
            )

            reward += 10

        # ==================================================
        # EXIT
        # ==================================================

        if (
            new_x,
            new_y
        ) == self.exit_position:

            reward += 100

            return (
                True,
                reward,
                True
            )

        return (
            True,
            reward,
            False
        )

    # ==================================================
    # GET NEIGHBORS
    # ==================================================

    def get_neighbors(self):

        x, y = (
            self.pacman_position
        )

        directions = {

            "UP": (
                0,
                -1
            ),

            "DOWN": (
                0,
                1
            ),

            "LEFT": (
                -1,
                0
            ),

            "RIGHT": (
                1,
                0
            )
        }

        neighbors = {}

        for direction, (
            dx,
            dy
        ) in directions.items():

            new_x = (
                x + dx
            )

            new_y = (
                y + dy
            )

            if self.is_walkable(
                new_x,
                new_y
            ):

                neighbors[
                    direction
                ] = (
                    new_x,
                    new_y
                )

        return neighbors

    # ==================================================
    # GHOST LINE OF SIGHT
    # ==================================================

    def ghost_can_see_pacman(
        self,
        ghost_position
    ):

        gx, gy = ghost_position

        px, py = (
            self.pacman_position
        )

        # --------------------------------------------------
        # SAME ROW
        # --------------------------------------------------

        if gy == py:

            step = (
                1
                if px > gx
                else -1
            )

            for x in range(
                gx + step,
                px,
                step
            ):

                if self.maze[gy][x] == "#":

                    return False

            return True

        # --------------------------------------------------
        # SAME COLUMN
        # --------------------------------------------------

        if gx == px:

            step = (
                1
                if py > gy
                else -1
            )

            for y in range(
                gy + step,
                py,
                step
            ):

                if self.maze[y][gx] == "#":

                    return False

            return True

        return False

    # ==================================================
    # MOVE GHOST TOWARD TARGET
    # ==================================================

    def move_ghost_toward(
        self,
        ghost_position,
        target,
        occupied
    ):

        gx, gy = ghost_position

        tx, ty = target

        possible_moves = []

        # --------------------------------------------------
        # PREFER MOVES TOWARD TARGET
        # --------------------------------------------------

        candidates = []

        if tx != gx:

            candidates.append(
                (
                    gx
                    + (
                        1
                        if tx > gx
                        else -1
                    ),
                    gy
                )
            )

        if ty != gy:

            candidates.append(
                (
                    gx,
                    gy
                    + (
                        1
                        if ty > gy
                        else -1
                    )
                )
            )

        # --------------------------------------------------
        # FALLBACK DIRECTIONS
        # --------------------------------------------------

        candidates += [

            (
                gx + 1,
                gy
            ),

            (
                gx - 1,
                gy
            ),

            (
                gx,
                gy + 1
            ),

            (
                gx,
                gy - 1
            )
        ]

        # Remove duplicates while preserving order.
        seen = set()

        unique_candidates = []

        for candidate in candidates:

            if candidate in seen:
                continue

            seen.add(
                candidate
            )

            unique_candidates.append(
                candidate
            )

        # --------------------------------------------------
        # FIND VALID MOVE
        # --------------------------------------------------

        for new_x, new_y in (
            unique_candidates
        ):

            if (
                new_y < 0
                or new_y >= len(
                    self.maze
                )
            ):
                continue

            if (
                new_x < 0
                or new_x >= len(
                    self.maze[0]
                )
            ):
                continue

            if self.maze[
                new_y
            ][
                new_x
            ] == "#":

                continue

            if (
                new_x,
                new_y
            ) in occupied:

                continue

            if (
                new_x,
                new_y
            ) == self.pacman_position:

                return (
                    new_x,
                    new_y
                )

            possible_moves.append(
                (
                    new_x,
                    new_y
                )
            )

        if possible_moves:

            return possible_moves[0]

        return ghost_position

    # ==================================================
    # MOVE GHOSTS
    # ==================================================

    def move_ghosts(self):

        directions = [

            (
                1,
                0
            ),

            (
                -1,
                0
            ),

            (
                0,
                1
            ),

            (
                0,
                -1
            )
        ]

        # The controller calls this once per decision tick.  Ghosts act on
        # three ticks, then skip one, for a deterministic 75% cadence.
        self.ghost_tick += 1

        if self.ghost_tick % 4 == 0:
            return

        new_positions = []

        for i, ghost_position in enumerate(
            self.ghost_positions
        ):

            # ==================================================
            # SEE PAC-MAN
            # ==================================================

            if self.ghost_can_see_pacman(
                ghost_position
            ):

                self.ghost_last_known[i] = (
                    self.pacman_position
                )

            target = (
                self.ghost_last_known[i]
            )

            # ==================================================
            # CHASE / SEARCH
            # ==================================================

            if target is not None:

                new_position = (
                    self.move_ghost_toward(
                        ghost_position,
                        target,
                        new_positions
                    )
                )

                if (
                    new_position
                    == target
                ):

                    self.ghost_last_known[i] = None

            # ==================================================
            # RANDOM WANDER
            # ==================================================

            else:

                possible_moves = []

                gx, gy = (
                    ghost_position
                )

                for dx, dy in directions:

                    new_x = (
                        gx + dx
                    )

                    new_y = (
                        gy + dy
                    )

                    if (
                        new_y < 0
                        or new_y >= len(
                            self.maze
                        )
                    ):
                        continue

                    if (
                        new_x < 0
                        or new_x >= len(
                            self.maze[0]
                        )
                    ):
                        continue

                    if self.maze[
                        new_y
                    ][
                        new_x
                    ] == "#":

                        continue

                    if (
                        new_x,
                        new_y
                    ) in new_positions:

                        continue

                    # Ghosts can occupy Pac-Man's
                    # current cell. Collision is checked
                    # separately.
                    possible_moves.append(
                        (
                            new_x,
                            new_y
                        )
                    )

                if possible_moves:

                    new_position = (
                        random.choice(
                            possible_moves
                        )
                    )

                else:

                    new_position = (
                        ghost_position
                    )

            new_positions.append(
                new_position
            )

        self.ghost_positions = (
            new_positions
        )

    # ==================================================
    # GHOST COLLISION
    # ==================================================

    def check_ghost_collision(self):

        return (
            self.pacman_position
            in self.ghost_positions
        )

    # ==================================================
    # DEBUG DISPLAY
    # ==================================================

    def get_display_maze(self):

        """
        Create a temporary display representation.

        This DOES NOT modify self.maze.

        P = Pac-Man
        G = ghost
        o = pellet
        E = exit
        """

        display = [
            row[:]
            for row in self.maze
        ]

        # Pellets
        for x, y in self.pellets:

            if (
                0 <= y < len(display)
                and 0 <= x < len(display[0])
            ):

                display[y][x] = "o"

        # Exit
        if self.exit_position is not None:

            ex, ey = (
                self.exit_position
            )

            display[ey][ex] = "E"

        # Ghosts
        for x, y in (
            self.ghost_positions
        ):

            display[y][x] = "G"

        # Pac-Man
        if self.pacman_position is not None:

            px, py = (
                self.pacman_position
            )

            display[py][px] = "P"

        return display


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    from maze import (
        generate_maze,
        print_maze
    )

    maze = generate_maze()

    world = World(
        maze
    )

    print(
        "Initial world:"
    )

    print_maze(
        world.get_display_maze()
    )

    print()

    print(
        "Pac-Man position:",
        world.pacman_position
    )

    print(
        "Exit position:",
        world.exit_position
    )

    print(
        "Ghost positions:",
        world.ghost_positions
    )

    print(
        "Pellets:",
        len(world.pellets)
    )

    print()

    print(
        "Available moves:"
    )

    for direction, position in (
        world.get_neighbors().items()
    ):

        print(
            f"{direction}: {position}"
        )
