class RuleBasedBrain:

    def __init__(self):
        self.last_action = None
        self.visited = {}

    def choose_action(self, vision, position):

        self.visited[position] = self.visited.get(position, 0) + 1

        scores = {}

        opposite = {
            "UP": "DOWN",
            "DOWN": "UP",
            "LEFT": "RIGHT",
            "RIGHT": "LEFT"
        }

        for direction, cells in vision.items():

            # Can't move
            if not cells:
                continue

            # Wall immediately ahead
            if cells[0] == "#":
                continue

            score = 0

            # --------------------------------
            # Look at what is ahead
            # --------------------------------

            for distance, cell in enumerate(cells, start=1):

                if cell == "o":
                    score += 10 / distance

                elif cell == "G":
                    score -= 100 / distance

            # --------------------------------
            # Don't immediately reverse
            # --------------------------------

            if self.last_action is not None:

                if direction == opposite[self.last_action]:
                    score -= 5

            # --------------------------------
            # Exploration
            # --------------------------------

            # Estimate the position one step ahead
            dx, dy = {
                "UP": (0, -1),
                "DOWN": (0, 1),
                "LEFT": (-1, 0),
                "RIGHT": (1, 0)
            }[direction]

            next_position = (
                position[0] + dx,
                position[1] + dy
            )

            visits = self.visited.get(next_position, 0)

            # Penalize places we've already visited
            score -= visits * 2

            scores[direction] = score

        # No possible moves
        if not scores:
            return None

        # Choose best direction
        best_direction = max(
            scores,
            key=scores.get
        )

        # Remember our move
        self.last_action = best_direction

        return best_direction