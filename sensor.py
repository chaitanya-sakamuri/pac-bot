class CardinalSensor:

    def __init__(self, world, max_range=8):
        self.world = world
        self.max_range = max_range

    def get_cell(self, x, y):

        # Ghost
        if (x, y) in self.world.ghost_positions:
            return "G"

        # Pellet
        if (x, y) in self.world.pellets:
            return "o"

        # Exit
        if (x, y) == self.world.exit_position:
            return "E"

        # Normal maze cell
        return self.world.maze[y][x]

    def scan_direction(self, dx, dy):

        x, y = self.world.pacman_position

        vision = []

        for distance in range(1, self.max_range + 1):

            new_x = x + dx * distance
            new_y = y + dy * distance

            # Outside maze
            if (
                new_x < 0
                or new_x >= len(self.world.maze[0])
                or new_y < 0
                or new_y >= len(self.world.maze)
            ):
                break

            cell = self.get_cell(new_x, new_y)

            # Wall blocks vision
            if cell == "#":
                vision.append("#")
                break

            vision.append(cell)

        return vision

    def scan(self):

        return {
            "UP": self.scan_direction(0, -1),
            "DOWN": self.scan_direction(0, 1),
            "LEFT": self.scan_direction(-1, 0),
            "RIGHT": self.scan_direction(1, 0)
        }