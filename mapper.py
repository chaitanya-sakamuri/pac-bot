class Mapper:

    def __init__(self):
        # Coordinates Pac-Bot has discovered
        self.map = {}

        # Total number of cells discovered
        self.discovered = 0

    def update(self, vision, pacman_position):

        x, y = pacman_position

        directions = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0)
        }

        new_cells = 0

        # Pac-Man knows where he currently is
        if (x, y) not in self.map:
            self.map[(x, y)] = "P"
            self.discovered += 1
            new_cells += 1

        # Process sensor information
        for direction, cells in vision.items():

            dx, dy = directions[direction]

            for distance, cell in enumerate(cells, start=1):

                cell_x = x + dx * distance
                cell_y = y + dy * distance

                # Only reward first-time discoveries
                if (cell_x, cell_y) not in self.map:

                    self.map[(cell_x, cell_y)] = cell

                    self.discovered += 1
                    new_cells += 1

                else:
                    # Update what we already know
                    self.map[(cell_x, cell_y)] = cell

        # Exploration reward
        reward = new_cells * 0.1

        return reward, new_cells

    def display_map(self):

        if not self.map:
            return

        xs = [x for x, y in self.map]
        ys = [y for x, y in self.map]

        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)

        print("\n========== PAC-BOT MEMORY ==========\n")

        for y in range(min_y, max_y + 1):

            row = ""

            for x in range(min_x, max_x + 1):

                cell = self.map.get((x, y), "?")

                row += cell

            print(row)

        print()
        print("Cells discovered:", self.discovered)
