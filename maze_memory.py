from collections import deque
import heapq


class MazeMemory:

    UNKNOWN = "?"
    WALL = "#"
    FLOOR = " "
    PELLET = "o"
    EXIT = "E"

    DIRECTIONS = {
        "UP": (0, -1),
        "DOWN": (0, 1),
        "LEFT": (-1, 0),
        "RIGHT": (1, 0)
    }

    WALKABLE = {
        FLOOR,
        PELLET,
        EXIT
    }

    def __init__(self):

        # ==================================================
        # PERMANENT MAP
        # ==================================================

        # (x, y) -> known static cell type
        #
        # IMPORTANT:
        # Ghosts are NOT stored here.
        #
        self.map = {}

        # Number of unique cells ever discovered.
        self.discovered = 0

        # ==================================================
        # EXPLORATION MEMORY
        # ==================================================

        # (x, y) -> number of physical visits
        self.visited = {}

        # Cells physically visited at least once.
        self.explored = set()

        # Order in which cells were first discovered.
        self.discovery_order = []

        # ==================================================
        # MAP STATISTICS
        # ==================================================

        self.total_walkable_discovered = 0
        self.total_walls_discovered = 0

    # ==================================================
    # UPDATE MEMORY FROM SENSOR
    # ==================================================


    def get_cell(self, position):
        return self.map.get(
            position,
            self.UNKNOWN
        )

    def update(
        self,
        vision,
        pacman_position
    ):

        x, y = pacman_position

        new_cells = 0

        # ==================================================
        # CURRENT POSITION
        # ==================================================

        self._record_discovery(
            pacman_position,
            self.FLOOR
        )

        self.record_visit(
            pacman_position
        )

        # ==================================================
        # SENSOR INFORMATION
        # ==================================================

        for direction, cells in vision.items():

            dx, dy = self.DIRECTIONS[
                direction
            ]

            for distance, observed_cell in enumerate(
                cells,
                start=1
            ):

                position = (
                    x + dx * distance,
                    y + dy * distance
                )

                # --------------------------------------------------
                # WALL
                # --------------------------------------------------

                if observed_cell == self.WALL:

                    if self._record_discovery(
                        position,
                        self.WALL
                    ):
                        new_cells += 1

                    # Nothing beyond a wall is visible.
                    break

                # --------------------------------------------------
                # EXIT
                # --------------------------------------------------

                elif observed_cell == self.EXIT:

                    if self._record_discovery(
                        position,
                        self.EXIT
                    ):
                        new_cells += 1

                    else:

                        # Exit is permanent knowledge.
                        self.map[position] = self.EXIT

                # --------------------------------------------------
                # PELLET
                # --------------------------------------------------

                elif observed_cell == self.PELLET:

                    if self._record_discovery(
                        position,
                        self.PELLET
                    ):
                        new_cells += 1

                    elif position not in self.explored:

                        # Pellet still exists if Pac-Man has
                        # not physically visited the cell.
                        self.map[position] = self.PELLET

                # --------------------------------------------------
                # GHOST
                # --------------------------------------------------

                elif observed_cell == "G":

                    # IMPORTANT:
                    #
                    # Ghosts are dynamic.
                    # They NEVER enter the permanent map.
                    #
                    # We simply know the underlying cell
                    # is walkable.
                    #
                    if position not in self.map:

                        if self._record_discovery(
                            position,
                            self.FLOOR
                        ):
                            new_cells += 1

                    elif self.map[position] == self.UNKNOWN:

                        self.map[position] = self.FLOOR

                # --------------------------------------------------
                # NORMAL FLOOR
                # --------------------------------------------------

                else:

                    if self._record_discovery(
                        position,
                        self.FLOOR
                    ):
                        new_cells += 1

                    elif position not in self.explored:

                        # Never overwrite permanent special cells.
                        if self.map[position] not in (
                            self.EXIT,
                            self.PELLET
                        ):
                            self.map[position] = self.FLOOR

        exploration_reward = (
            new_cells * 0.1
        )

        return (
            exploration_reward,
            new_cells
        )

    # ==================================================
    # INTERNAL DISCOVERY
    # ==================================================

    def _record_discovery(
        self,
        position,
        cell_type
    ):

        if position not in self.map:

            self.map[position] = cell_type

            self.discovered += 1

            self.discovery_order.append(
                position
            )

            if cell_type == self.WALL:

                self.total_walls_discovered += 1

            else:

                self.total_walkable_discovered += 1

            return True

        # Existing cell:
        # update its known static information.
        #
        # Never allow a normal floor observation to
        # erase an EXIT or PELLET.
        if cell_type == self.WALL:

            self.map[position] = self.WALL

        elif self.map[position] not in (
            self.WALL,
            self.EXIT,
            self.PELLET
        ):

            self.map[position] = cell_type

        return False

    # ==================================================
    # VISIT MEMORY
    # ==================================================

    def record_visit(
        self,
        position
    ):

        self.visited[position] = (
            self.visited.get(
                position,
                0
            ) + 1
        )

        self.explored.add(
            position
        )

        # A physically visited cell is known to be
        # walkable.
        #
        # Never overwrite a wall.
        #
        # Never erase the exit.

        if self.map.get(position) == self.WALL:
            return

        if self.map.get(position) == self.EXIT:
            return

        self.map[position] = self.FLOOR

    # ==================================================
    # VISIT COUNT
    # ==================================================

    def get_visit_count(
        self,
        position
    ):

        return self.visited.get(
            position,
            0
        )

    # ==================================================
    # VISIT HEAT
    # ==================================================

    def visit_heat(
        self,
        position
    ):

        """
        Returns a normalized measure of how often
        Pac-Man has visited a cell.

        Useful for detecting repeatedly visited areas.
        """

        visits = self.get_visit_count(
            position
        )

        if visits <= 0:
            return 0.0

        return min(
            visits / 10.0,
            1.0
        )

    # ==================================================
    # KNOWN PELLETS
    # ==================================================

    def known_pellets(self):

        return [
            position
            for position, cell
            in self.map.items()
            if cell == self.PELLET
            and position not in self.explored
        ]

    # ==================================================
    # FIND EXIT
    # ==================================================

    def find_exit(self):

        for position, cell in self.map.items():

            if cell == self.EXIT:

                return position

        return None

    # ==================================================
    # IS WALKABLE
    # ==================================================

    def is_walkable(
        self,
        position
    ):

        return (
            self.map.get(
                position,
                self.UNKNOWN
            )
            in self.WALKABLE
        )

    # ==================================================
    # IS KNOWN
    # ==================================================

    def is_known(
        self,
        position
    ):

        return position in self.map

    # ==================================================
    # IS EXPLORED
    # ==================================================

    def is_explored(
        self,
        position
    ):

        return position in self.explored

    # ==================================================
    # IS UNKNOWN
    # ==================================================

    def is_unknown(
        self,
        position
    ):

        return position not in self.map

    # ==================================================
    # FRONTIER CELLS
    # ==================================================

    def frontier_cells(self):

        """
        A frontier is a KNOWN WALKABLE cell adjacent
        to at least one UNKNOWN cell.

        These are the places from which Pac-Man can
        expand his internal map.
        """

        frontiers = []

        for position, cell in self.map.items():

            if cell not in self.WALKABLE:
                continue

            x, y = position

            for dx, dy in self.DIRECTIONS.values():

                neighbour = (
                    x + dx,
                    y + dy
                )

                if neighbour not in self.map:

                    frontiers.append(
                        position
                    )

                    break

        return frontiers

    # ==================================================
    # FRONTIER INFORMATION
    # ==================================================

    def frontier_unknown_count(
        self,
        position
    ):

        """
        How many immediately adjacent cells are unknown?
        """

        x, y = position

        count = 0

        for dx, dy in self.DIRECTIONS.values():

            neighbour = (
                x + dx,
                y + dy
            )

            if neighbour not in self.map:

                count += 1

        return count

    # ==================================================
    # FRONTIER SCORE
    # ==================================================

    def frontier_value(
        self,
        position
    ):

        """
        Higher = potentially more useful for exploration.

        This does NOT decide where Pac-Man goes.
        It simply describes how informative the frontier is.
        """

        unknown_count = (
            self.frontier_unknown_count(
                position
            )
        )

        visits = self.get_visit_count(
            position
        )

        return (
            unknown_count * 10
            - visits * 2
        )

    # ==================================================
    # NEIGHBOURS
    # ==================================================

    def neighbours(
        self,
        position,
        walkable_only=False
    ):

        x, y = position

        result = []

        for dx, dy in self.DIRECTIONS.values():

            neighbour = (
                x + dx,
                y + dy
            )

            if walkable_only:

                if not self.is_walkable(
                    neighbour
                ):
                    continue

            result.append(
                neighbour
            )

        return result

    # ==================================================
    # BFS PATH
    # ==================================================

    def bfs_path(
        self,
        start,
        goal,
        allow_unknown=False
    ):

        if start == goal:

            return [start]

        passable = set(
            self.WALKABLE
        )

        queue = deque(
            [start]
        )

        came_from = {
            start: None
        }

        while queue:

            current = queue.popleft()

            for neighbour in self.neighbours(
                current
            ):

                if neighbour in came_from:
                    continue

                cell = self.map.get(
                    neighbour,
                    self.UNKNOWN
                )

                if cell in passable:

                    came_from[
                        neighbour
                    ] = current

                    queue.append(
                        neighbour
                    )

                elif (
                    allow_unknown
                    and cell == self.UNKNOWN
                ):

                    came_from[
                        neighbour
                    ] = current

                    queue.append(
                        neighbour
                    )

        if goal not in came_from:

            return None

        return self._reconstruct_path(
            came_from,
            goal
        )

    # ==================================================
    # A* PATH
    # ==================================================

    def astar_path(
        self,
        start,
        goal,
        blocked=None,
        allow_unknown=False
    ):

        """
        A* through the internal map.

        blocked:
            optional set of temporary dangerous cells.

        Unknown cells are not traversed unless
        allow_unknown=True.
        """

        if start == goal:

            return [start]

        blocked = (
            blocked
            if blocked is not None
            else set()
        )

        open_heap = []

        heapq.heappush(
            open_heap,
            (
                0,
                start
            )
        )

        came_from = {}

        g_score = {
            start: 0
        }

        closed = set()

        while open_heap:

            _, current = heapq.heappop(
                open_heap
            )

            if current in closed:
                continue

            closed.add(
                current
            )

            if current == goal:

                return self._reconstruct_path(
                    came_from,
                    goal
                )

            for neighbour in self.neighbours(
                current
            ):

                if neighbour in blocked:
                    continue

                if neighbour in closed:
                    continue

                cell = self.map.get(
                    neighbour,
                    self.UNKNOWN
                )

                if cell not in self.WALKABLE:

                    if not (
                        allow_unknown
                        and cell == self.UNKNOWN
                    ):
                        continue

                tentative_g = (
                    g_score[current] + 1
                )

                if tentative_g >= g_score.get(
                    neighbour,
                    float("inf")
                ):
                    continue

                came_from[
                    neighbour
                ] = current

                g_score[
                    neighbour
                ] = tentative_g

                f_score = (
                    tentative_g
                    + self.manhattan_distance(
                        neighbour,
                        goal
                    )
                )

                heapq.heappush(
                    open_heap,
                    (
                        f_score,
                        neighbour
                    )
                )

        return None

    # ==================================================
    # NEAREST TARGET
    # ==================================================

    def bfs_nearest(
        self,
        start,
        targets
    ):

        if not targets:

            return None, None

        targets = set(
            targets
        )

        queue = deque(
            [start]
        )

        came_from = {
            start: None
        }

        while queue:

            current = queue.popleft()

            if (
                current in targets
                and current != start
            ):

                return (
                    current,
                    self._reconstruct_path(
                        came_from,
                        current
                    )
                )

            for neighbour in self.neighbours(
                current,
                walkable_only=True
            ):

                if neighbour in came_from:
                    continue

                came_from[
                    neighbour
                ] = current

                queue.append(
                    neighbour
                )

        return None, None

    # ==================================================
    # REACHABLE CELLS
    # ==================================================

    def reachable_cells(
        self,
        start
    ):

        """
        Returns every currently known walkable cell
        reachable from start.
        """

        if not self.is_walkable(start):

            # Pac-Man's current cell may not have been
            # explicitly classified yet.
            if start not in self.map:
                return set()

        reachable = {
            start
        }

        queue = deque(
            [start]
        )

        while queue:

            current = queue.popleft()

            for neighbour in self.neighbours(
                current,
                walkable_only=True
            ):

                if neighbour in reachable:
                    continue

                reachable.add(
                    neighbour
                )

                queue.append(
                    neighbour
                )

        return reachable

    # ==================================================
    # UNKNOWN BORDER CELLS
    # ==================================================

    def unknown_neighbours(
        self,
        position
    ):

        x, y = position

        unknown = []

        for dx, dy in self.DIRECTIONS.values():

            neighbour = (
                x + dx,
                y + dy
            )

            if neighbour not in self.map:

                unknown.append(
                    neighbour
                )

        return unknown

    # ==================================================
    # EXPLORED RATIO
    # ==================================================

    def exploration_ratio(self):

        if self.discovered == 0:

            return 0.0

        explored_walkable = len(
            self.explored
        )

        if self.total_walkable_discovered == 0:

            return 0.0

        return (
            explored_walkable
            / self.total_walkable_discovered
        )

    # ==================================================
    # MANHATTAN DISTANCE
    # ==================================================

    @staticmethod
    def manhattan_distance(
        a,
        b
    ):

        return (
            abs(a[0] - b[0])
            + abs(a[1] - b[1])
        )

    # ==================================================
    # PATH RECONSTRUCTION
    # ==================================================

    @staticmethod
    def _reconstruct_path(
        came_from,
        goal
    ):

        path = [
            goal
        ]

        current = goal

        while current in came_from:

            current = came_from[
                current
            ]

            if current is None:
                break

            path.append(
                current
            )

        path.reverse()

        return path

    # ==================================================
    # DIRECTION TO NEIGHBOUR
    # ==================================================

    def direction_to(
        self,
        current,
        target
    ):

        dx = (
            target[0]
            - current[0]
        )

        dy = (
            target[1]
            - current[1]
        )

        for direction, (
            ddx,
            ddy
        ) in self.DIRECTIONS.items():

            if (
                dx == ddx
                and dy == ddy
            ):

                return direction

        return None

    # ==================================================
    # MAP COMPLETENESS
    # ==================================================

    def map_summary(self):

        return {
            "discovered": self.discovered,
            "explored": len(
                self.explored
            ),
            "known_walkable":
                self.total_walkable_discovered,
            "known_walls":
                self.total_walls_discovered,
            "known_pellets":
                len(
                    self.known_pellets()
                ),
            "frontiers":
                len(
                    self.frontier_cells()
                ),
            "exit_known":
                self.find_exit() is not None
        }

    # ==================================================
    # DISPLAY MEMORY
    # ==================================================

    def display_map(
        self
    ):

        if not self.map:

            return

        xs = [
            x
            for x, y in self.map
        ]

        ys = [
            y
            for x, y in self.map
        ]

        min_x = min(xs)
        max_x = max(xs)

        min_y = min(ys)
        max_y = max(ys)

        print(
            "\n========== PAC-BOT MEMORY ==========\n"
        )

        for y in range(
            min_y,
            max_y + 1
        ):

            row = ""

            for x in range(
                min_x,
                max_x + 1
            ):

                cell = self.map.get(
                    (x, y),
                    self.UNKNOWN
                )

                # Show frequently visited cells
                # differently to make loops visible.
                if (
                    cell == self.FLOOR
                    and self.get_visit_count(
                        (x, y)
                    ) >= 5
                ):

                    row += "."

                else:

                    row += cell

            print(
                row
            )

        print()

        summary = (
            self.map_summary()
        )

        print(
            "Cells discovered:",
            summary["discovered"]
        )

        print(
            "Cells explored:",
            summary["explored"]
        )

        print(
            "Known walkable:",
            summary["known_walkable"]
        )

        print(
            "Known walls:",
            summary["known_walls"]
        )

        print(
            "Known pellets:",
            summary["known_pellets"]
        )

        print(
            "Frontiers:",
            summary["frontiers"]
        )

        print(
            "Exit known:",
            summary["exit_known"]
        )