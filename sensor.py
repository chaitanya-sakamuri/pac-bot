class CardinalSensor:

    def __init__(self, world, max_range=8):
        self.world = world
        self.max_range = max_range

    def scan_direction(self, dx, dy):

        x, y = self.world.pacman_position

        vision = []

        for distance in range(1, self.max_range + 1):

            new_x = x + dx * distance
            new_y = y + dy * distance

            # Outside the maze
            if (
                new_x < 0
                or new_x >= len(self.world.maze[0])
                or new_y < 0
                or new_y >= len(self.world.maze)
            ):
                break

            # Wall blocks vision
            if self.world.maze[new_y][new_x] == "#":
                vision.append("#")
                break

            # Ghost
            if (new_x, new_y) in self.world.ghost_positions:
                vision.append("G")
                continue

            # Pellet
            if (new_x, new_y) in self.world.pellets:
                vision.append("o")
                continue

            # Empty floor
            vision.append(".")

        return vision

    def scan(self):

        return {
            "UP": self.scan_direction(0, -1),
            "DOWN": self.scan_direction(0, 1),
            "LEFT": self.scan_direction(-1, 0),
            "RIGHT": self.scan_direction(1, 0)
        }