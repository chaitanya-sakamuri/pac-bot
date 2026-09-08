class CardinalSensor:

    def __init__(
        self,
        world,
        max_range=8
    ):

        self.world = world
        self.max_range = max_range

    # ==================================================
    # GET CELL
    # ==================================================

    def get_cell(
        self,
        x,
        y
    ):

        # --------------------------------------------------
        # GHOST
        # --------------------------------------------------
        #
        # The world.ghost_positions list is the ONLY
        # authority for current ghost positions.
        #
        # Never trust a "G" stored in the maze itself.
        #

        if (
            x,
            y
        ) in self.world.ghost_positions:

            return "G"

        # --------------------------------------------------
        # PELLET
        # --------------------------------------------------

        if (
            x,
            y
        ) in self.world.pellets:

            return "o"

        # --------------------------------------------------
        # EXIT
        # --------------------------------------------------

        if (
            x,
            y
        ) == self.world.exit_position:

            return "E"

        # --------------------------------------------------
        # MAZE
        # --------------------------------------------------

        cell = self.world.maze[y][x]

        # A stale G inside the maze is just a normal
        # underlying walkable cell.
        if cell == "G":

            return "."

        return cell

    # ==================================================
    # SCAN ONE DIRECTION
    # ==================================================

    def scan_direction(
        self,
        dx,
        dy
    ):

        x, y = self.world.pacman_position

        vision = []

        for distance in range(
            1,
            self.max_range + 1
        ):

            new_x = (
                x + dx * distance
            )

            new_y = (
                y + dy * distance
            )

            # --------------------------------------------------
            # OUTSIDE MAZE
            # --------------------------------------------------

            if (
                new_x < 0
                or new_x >= len(
                    self.world.maze[0]
                )
                or new_y < 0
                or new_y >= len(
                    self.world.maze
                )
            ):

                break

            cell = self.get_cell(
                new_x,
                new_y
            )

            # --------------------------------------------------
            # WALL
            # --------------------------------------------------

            if cell == "#":

                vision.append(
                    "#"
                )

                # A wall blocks everything behind it.
                break

            # --------------------------------------------------
            # VISIBLE CELL
            # --------------------------------------------------

            vision.append(
                cell
            )

        return vision

    # ==================================================
    # FULL CARDINAL VISION
    # ==================================================

    def scan(self):

        return {

            "UP": self.scan_direction(
                0,
                -1
            ),

            "DOWN": self.scan_direction(
                0,
                1
            ),

            "LEFT": self.scan_direction(
                -1,
                0
            ),

            "RIGHT": self.scan_direction(
                1,
                0
            )
        }

    # ==================================================
    # GHOST DETECTION
    # ==================================================

    def visible_ghosts(self):

        vision = self.scan()

        ghosts = []

        px, py = (
            self.world.pacman_position
        )

        directions = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        for direction, cells in vision.items():

            dx, dy = directions[
                direction
            ]

            for distance, cell in enumerate(
                cells,
                start=1
            ):

                if cell == "#":
                    break

                if cell == "G":

                    ghosts.append(
                        (
                            px + dx * distance,
                            py + dy * distance
                        )
                    )

                    break

        return ghosts

    # ==================================================
    # NEAREST GHOST DISTANCE
    # ==================================================

    def nearest_ghost_distance(self):

        vision = self.scan()

        nearest = None

        for cells in vision.values():

            for distance, cell in enumerate(
                cells,
                start=1
            ):

                if cell == "#":
                    break

                if cell == "G":

                    if nearest is None:

                        nearest = distance

                    else:

                        nearest = min(
                            nearest,
                            distance
                        )

                    break

        return nearest