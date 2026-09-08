import time
import os
import random

from maze import generate_maze
from world import World
from sensor import CardinalSensor
from maze_memory import MazeMemory
from ghost_qbrain import GhostQLearningBrain


# ============================================================
# SETTINGS
# ============================================================

TRAINING_EPISODES = 0

# Presentation-only delay; simulation still advances one decision tick per
# loop iteration.
STEP_DELAY = 0.10

MAX_TRAINING_STEPS = 3000
MAX_TEST_STEPS = 3000

SENSOR_RANGE = 8

GHOST_DANGER_RADIUS = 5

# Recently seen ghost locations remain temporarily dangerous.
GHOST_MEMORY_STEPS = 12

# Smaller than before.
# We don't want the entire maze becoming "forbidden".
GHOST_MEMORY_RADIUS = 2

GHOST_QTABLE_FILE = "ghost_qtable.pkl"
# ============================================================
# PELLET DETOUR
# ============================================================
pellet_detour_target = None
interrupted_navigation_target = None

# Persistent A* navigation state.
navigation_target = None
navigation_path = None


# ============================================================
# REWARDS
# ============================================================

STEP_PENALTY = -0.02

NEW_CELL_REWARD = 0.20
MAX_EXPLORATION_REWARD = 1.0

GHOST_VISIBLE_REWARD = 0.05
GHOST_COLLISION_REWARD = -100.0

REVERSAL_PENALTY = -0.5


# ============================================================
# DIRECTIONS
# ============================================================

DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0)
}


OPPOSITE = {
    "UP": "DOWN",
    "DOWN": "UP",
    "LEFT": "RIGHT",
    "RIGHT": "LEFT"
}


# ============================================================
# COLORS
# ============================================================

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


# ============================================================
# SCREEN
# ============================================================

def clear_screen():

    print(
        "\033[2J\033[H",
        end=""
    )


# ============================================================
# DISPLAY WORLD
# ============================================================

def display_world(world):

    display = [
        row[:]
        for row in world.maze
    ]

    # Hide static P/G/E symbols from base maze.
    for y in range(len(display)):

        for x in range(len(display[y])):

            if display[y][x] in (
                "P",
                "G",
                "E"
            ):

                display[y][x] = " "

    # Pellets
    for x, y in world.pellets:

        display[y][x] = (
            f"{YELLOW}o{RESET}"
        )

    # Ghosts
    for x, y in world.ghost_positions:

        if (x, y) != world.pacman_position:

            display[y][x] = (
                f"{RED}G{RESET}"
            )

    # Exit
    ex, ey = world.exit_position

    if (ex, ey) != world.pacman_position:

        display[ey][ex] = (
            f"{GREEN}E{RESET}"
        )

    # Pac-Man
    px, py = world.pacman_position

    display[py][px] = (
        f"{RED}P{RESET}"
    )

    for row in display:

        print(
            "".join(row)
        )


# ============================================================
# SAVE / LOAD Q TABLE
# ============================================================

def save_ghost_brain(brain):

    brain.save(
        GHOST_QTABLE_FILE
    )


def load_ghost_brain(brain):

    if not os.path.exists(
        GHOST_QTABLE_FILE
    ):

        print(
            "No ghost Q-table found."
        )

        print(
            "Starting with a fresh Q-table.\n"
        )

        return

    if brain.load(
        GHOST_QTABLE_FILE
    ):

        print(
            "Ghost Q-table loaded!"
        )

        print(
            "States:",
            len(brain.q_table)
        )

        print(
            "Exploration:",
            round(
                brain.exploration_rate,
                4
            )
        )

        print()


# ============================================================
# DIRECTION FROM TWO CELLS
# ============================================================

def direction_to_next(
    current,
    next_position
):

    dx = (
        next_position[0]
        - current[0]
    )

    dy = (
        next_position[1]
        - current[1]
    )

    for direction, (
        ddx,
        ddy
    ) in DIRECTIONS.items():

        if dx == ddx and dy == ddy:

            return direction

    return None


# ============================================================
# TEMPORARY GHOST MEMORY
# ============================================================

def update_ghost_memory(
    vision,
    pacman_position,
    danger_memory,
    current_step
):

    """
    Remember recently seen ghost positions.

    This is NOT part of the permanent maze map.

    Ghost memory expires automatically.
    """

    px, py = pacman_position

    for direction, cells in vision.items():

        dx, dy = DIRECTIONS[direction]

        for distance, cell in enumerate(
            cells,
            start=1
        ):

            # Walls block vision.
            if cell == "#":
                break

            if cell == "G":

                ghost_x = (
                    px + dx * distance
                )

                ghost_y = (
                    py + dy * distance
                )

                # Remember the ghost itself
                # and a small area around it.
                for rx in range(
                    -GHOST_MEMORY_RADIUS,
                    GHOST_MEMORY_RADIUS + 1
                ):

                    for ry in range(
                        -GHOST_MEMORY_RADIUS,
                        GHOST_MEMORY_RADIUS + 1
                    ):

                        if (
                            abs(rx) + abs(ry)
                            > GHOST_MEMORY_RADIUS
                        ):
                            continue

                        position = (
                            ghost_x + rx,
                            ghost_y + ry
                        )

                        danger_memory[position] = (
                            current_step
                            + GHOST_MEMORY_STEPS
                        )

                break


def clean_ghost_memory(
    danger_memory,
    current_step
):

    expired = [
        position
        for position, expiry
        in danger_memory.items()
        if expiry <= current_step
    ]

    for position in expired:

        del danger_memory[position]


def is_dangerous(
    position,
    danger_memory,
    current_step
):

    expiry = danger_memory.get(
        position
    )

    if expiry is None:
        return False

    return expiry > current_step


# ============================================================
# LIVE GHOST DETECTION
# ============================================================

def visible_ghost_positions(
    vision,
    pacman_position
):

    px, py = pacman_position

    ghosts = []

    for direction, cells in vision.items():

        dx, dy = DIRECTIONS[direction]

        for distance, cell in enumerate(
            cells,
            start=1
        ):

            # Wall blocks vision.
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


def nearest_visible_ghost_distance(
    vision
):

    nearest = None

    for cells in vision.values():

        for distance, cell in enumerate(
            cells,
            start=1
        ):

            if cell == "G":

                if nearest is None:
                    nearest = distance

                else:
                    nearest = min(
                        nearest,
                        distance
                    )

                break

            if cell == "#":
                break

    return nearest


def ghost_is_dangerous(
    vision
):

    distance = (
        nearest_visible_ghost_distance(
            vision
        )
    )

    if distance is None:
        return False

    return (
        distance <= GHOST_DANGER_RADIUS
    )


# ============================================================
# VALID ACTIONS
# ============================================================

def get_valid_actions(world):

    """Use World's bounds/wall/ghost-aware legal-action authority."""

    return world.get_pacman_valid_actions()


# ============================================================
# HARD GHOST SAFETY
# ============================================================

def get_ghost_safe_actions(
    vision,
    valid_actions
):

    ghost_directions = []

    for direction, cells in vision.items():

        for cell in cells:

            if cell == "#":
                break

            if cell == "G":

                ghost_directions.append(
                    direction
                )

                break

    if not ghost_directions:

        return valid_actions

    safe_actions = [
        action
        for action in valid_actions
        if action not in ghost_directions
    ]

    # Never return nothing merely because
    # the ghost situation is bad.
    if not safe_actions:

        return valid_actions

    return safe_actions


# ============================================================
# EMERGENCY GHOST REFLEX
# ============================================================

def ghost_reflex_action(
    vision,
    valid_actions
):

    """
    Only activates when a ghost is adjacent.

    If the exact opposite direction is available,
    take it.

    Otherwise return None and let the higher-level
    system decide.
    """

    for direction, cells in vision.items():

        if not cells:
            continue

        if cells[0] != "G":
            continue

        escape = OPPOSITE[
            direction
        ]

        if escape in valid_actions:

            return escape

    return None


# ============================================================
# A* PATHFINDING THROUGH INTERNAL MAP
# ============================================================

def heuristic(
    a,
    b
):

    return (
        abs(a[0] - b[0])
        + abs(a[1] - b[1])
    )


def astar_path(
    memory,
    start,
    goal,
    danger_memory=None,
    current_step=0,
    allow_danger_goal=False
):

    """
    A* operates ONLY on Pac-Man's internal map.

    Unknown cells are NOT treated as walkable.

    This is important:
    Pac-Man must first discover a region before
    confidently navigating through it.
    """

    if start == goal:

        return [start]

    open_set = {
        start
    }

    came_from = {}

    g_score = {
        start: 0
    }

    f_score = {
        start: heuristic(
            start,
            goal
        )
    }

    while open_set:

        current = min(
            open_set,
            key=lambda position:
                f_score.get(
                    position,
                    float("inf")
                )
        )

        if current == goal:

            path = [
                current
            ]

            while current in came_from:

                current = came_from[
                    current
                ]

                path.append(
                    current
                )

            path.reverse()

            return path

        open_set.remove(
            current
        )

        x, y = current

        for dx, dy in DIRECTIONS.values():

            nxt = (
                x + dx,
                y + dy
            )

            # Unknown map cells cannot be
            # used by the navigator.
            if not memory.is_walkable(
                nxt
            ):
                continue

            # Temporary ghost danger.
            if (
                danger_memory is not None
                and is_dangerous(
                    nxt,
                    danger_memory,
                    current_step
                )
                and not (
                    allow_danger_goal
                    and nxt == goal
                )
            ):
                continue

            tentative_g = (
                g_score[current] + 1
            )

            if tentative_g < g_score.get(
                nxt,
                float("inf")
            ):

                came_from[nxt] = current

                g_score[nxt] = (
                    tentative_g
                )

                f_score[nxt] = (
                    tentative_g
                    + heuristic(
                        nxt,
                        goal
                    )
                )

                open_set.add(
                    nxt
                )

    return None


# ============================================================
# FRONTIER SCORING
# ============================================================

def frontier_score(
    memory,
    frontier,
    pacman_position,
    danger_memory,
    current_step
):

    """
    Score a frontier cheaply.

    Manhattan distance is a cheap ranking estimate.  `choose_frontier()`
    subsequently verifies candidates with A* so temporary ghost danger
    cannot select an unreachable target.
    """

    if is_dangerous(
        frontier,
        danger_memory,
        current_step
    ):

        return float("-inf")

    distance = heuristic(
        pacman_position,
        frontier
    )

    visit_count = (
        memory.get_visit_count(
            frontier
        )
    )

    x, y = frontier

    unknown_neighbors = 0

    for dx, dy in DIRECTIONS.values():

        neighbour = (
            x + dx,
            y + dy
        )

        if memory.get_cell(
            neighbour
        ) == memory.UNKNOWN:

            unknown_neighbors += 1

    # Bigger score = better frontier.
    return (
        unknown_neighbors * 8
        - distance * 1.0
        - visit_count * 1.5
    )


def choose_frontier(
    memory,
    pacman_position,
    danger_memory,
    current_step
):

    frontiers = memory.frontier_cells()

    if not frontiers:

        return None

    scored_frontiers = []

    for frontier in frontiers:

        score = frontier_score(
            memory,
            frontier,
            pacman_position,
            danger_memory,
            current_step
        )

        if score != float("-inf"):
            scored_frontiers.append((score, frontier))

    # A Manhattan score alone cannot tell whether temporary ghost danger has
    # disconnected the target.  Preserve the existing score, but only select
    # the best frontier that A* can currently reach.
    for _, frontier in sorted(
        scored_frontiers,
        key=lambda item: item[0],
        reverse=True
    ):

        if astar_path(
            memory,
            pacman_position,
            frontier,
            danger_memory,
            current_step
        ) is not None:

            return frontier

    return None


# ============================================================
# CHOOSE KNOWN PELLET
# ============================================================

def choose_pellet(
    memory,
    pacman_position,
    danger_memory,
    current_step
):

    pellets = memory.known_pellets()

    best_pellet = None
    best_path = None
    best_score = float("-inf")

    for pellet in pellets:

        if is_dangerous(
            pellet,
            danger_memory,
            current_step
        ):
            continue

        path = astar_path(
            memory,
            pacman_position,
            pellet,
            danger_memory,
            current_step
        )

        if path is None:
            continue

        distance = len(path) - 1

        # Pellet is useful, but exploration is
        # more important than blindly chasing it.
        score = (
            5.0
            - distance * 0.25
        )

        if score > best_score:

            best_score = score
            best_pellet = pellet
            best_path = path

    if best_pellet is None:

        return None

    if (
        best_path is None
        or len(best_path) < 2
    ):

        return None

    return direction_to_next(
        pacman_position,
        best_path[1]
    )


# ============================================================
# EXIT NAVIGATION
# ============================================================

def get_exit_action(
    memory,
    pacman_position,
    danger_memory,
    current_step
):

    exit_position = memory.find_exit()

    if exit_position is None:
        return None

    if exit_position == pacman_position:
        return None

    path = astar_path(
        memory,
        pacman_position,
        exit_position,
        danger_memory,
        current_step,
        allow_danger_goal=True
    )

    if path is None:
        return None

    if len(path) < 2:
        return None

    return direction_to_next(
        pacman_position,
        path[1]
    )



# ============================================================
# VISIBLE PELLET DETOUR
# ============================================================

def get_visible_pellets(
    vision,
    pacman_position
):

    """
    Find pellets currently visible to Pac-Man.

    Only cardinal sensor vision is used.
    Walls block the sensor.

    Returns:
        [(position, distance), ...]
    """

    px, py = pacman_position

    pellets = []

    for direction, cells in vision.items():

        dx, dy = DIRECTIONS[direction]

        for distance, cell in enumerate(
            cells,
            start=1
        ):

            # Wall blocks everything behind it.
            if cell == "#":
                break

            if cell == "o":

                position = (
                    px + dx * distance,
                    py + dy * distance
                )

                pellets.append(
                    (
                        position,
                        distance
                    )
                )

                # First pellet in a direction is
                # the only one we need.
                break

    return pellets


# ============================================================
# INTELLIGENT NAVIGATION
# ============================================================

def _path_is_valid(
    memory,
    path,
    pacman_position,
    danger_memory,
    current_step,
    allow_danger_goal=False
):

    """
    Check whether a cached A* path is still usable.

    We replan if:
    - the path is missing,
    - Pac-Man is no longer at the path start,
    - a cell became blocked/unknown,
    - a cell became temporarily dangerous.

    This lets us keep a path across frames while still reacting
    immediately to changing ghost danger.
    """

    if (
        path is None
        or len(path) < 2
    ):
        return False

    if path[0] != pacman_position:
        return False

    goal = path[-1]

    previous = path[0]

    for position in path[1:]:

        dx = abs(position[0] - previous[0])
        dy = abs(position[1] - previous[1])

        if dx + dy != 1:
            return False

        if not memory.is_walkable(
            position
        ):
            return False

        if (
            is_dangerous(
                position,
                danger_memory,
                current_step
            )
            and not (
                allow_danger_goal
                and position == goal
            )
        ):
            return False

        previous = position

    return True


def navigation_action(
    memory,
    pacman_position,
    danger_memory,
    current_step,
    prefer_exit=False
):

    """
    Persistent high-level navigation.

    A* is calculated when a target is selected or when the cached
    path becomes invalid.  Otherwise Pac-Man simply follows the
    existing path.

    Priority:
    1. Known exit.
    2. Existing exploration target.
    3. New exploration frontier.
    4. Known pellet fallback.
    5. Exit fallback.
    """

    global navigation_target
    global navigation_path

    # ========================================================
    # 1. EXIT IS KNOWN
    # ========================================================

    exit_position = memory.find_exit()

    if exit_position is not None:

        # The exit supersedes any exploration target.
        if navigation_target != exit_position:

            navigation_target = exit_position
            navigation_path = None

        if not _path_is_valid(
            memory,
            navigation_path,
            pacman_position,
            danger_memory,
            current_step,
            allow_danger_goal=True
        ):

            navigation_path = astar_path(
                memory,
                pacman_position,
                navigation_target,
                danger_memory,
                current_step,
                allow_danger_goal=True
            )

        if _path_is_valid(
            memory,
            navigation_path,
            pacman_position,
            danger_memory,
            current_step,
            allow_danger_goal=True
        ):

            action = direction_to_next(
                pacman_position,
                navigation_path[1]
            )

            if action is not None:

                return action, "EXIT A*"

        # Exit exists but cannot currently be reached.
        # Keep the target so it can be retried after danger changes.
        navigation_path = None

    # ========================================================
    # 2. KEEP FOLLOWING EXISTING EXPLORATION TARGET
    # ========================================================

    if (
        navigation_target is not None
        and navigation_target != exit_position
    ):

        # Target reached.
        if pacman_position == navigation_target:

            navigation_target = None
            navigation_path = None

        else:

            if not _path_is_valid(
                memory,
                navigation_path,
                pacman_position,
                danger_memory,
                current_step
            ):

                navigation_path = astar_path(
                    memory,
                    pacman_position,
                    navigation_target,
                    danger_memory,
                    current_step
                )

            if _path_is_valid(
                memory,
                navigation_path,
                pacman_position,
                danger_memory,
                current_step
            ):

                action = direction_to_next(
                    pacman_position,
                    navigation_path[1]
                )

                if action is not None:

                    return action, "EXPLORE A*"

            # Existing target became unreachable.
            navigation_target = None
            navigation_path = None

    # ========================================================
    # 3. SELECT A NEW EXPLORATION TARGET
    # ========================================================

    frontier = choose_frontier(
        memory,
        pacman_position,
        danger_memory,
        current_step
    )

    if frontier is not None:

        navigation_target = frontier

        navigation_path = astar_path(
            memory,
            pacman_position,
            navigation_target,
            danger_memory,
            current_step
        )

        if _path_is_valid(
            memory,
            navigation_path,
            pacman_position,
            danger_memory,
            current_step
        ):

            action = direction_to_next(
                pacman_position,
                navigation_path[1]
            )

            if action is not None:

                return action, "EXPLORE A*"

    # ========================================================
    # 4. KNOWN PELLET FALLBACK
    # ========================================================

    action = choose_pellet(
        memory,
        pacman_position,
        danger_memory,
        current_step
    )

    if action is not None:

        return action, "PELLET A*"

    # ========================================================
    # 5. EXIT FALLBACK
    # ========================================================

    action = get_exit_action(
        memory,
        pacman_position,
        danger_memory,
        current_step
    )

    if action is not None:

        return action, "EXIT A*"

    return None, "NO NAVIGATION"


def get_normal_navigation_target(
    memory,
    pacman_position,
    danger_memory,
    current_step
):

    """
    Return the destination that normal navigation should pursue.

    This intentionally does NOT run A*.  The caller will calculate
    the actual path only after the destination has been selected.
    """

    exit_position = memory.find_exit()

    if exit_position is not None:
        return exit_position

    return choose_frontier(
        memory,
        pacman_position,
        danger_memory,
        current_step
    )


def decide_action(
    memory,
    vision,
    world,
    pacman_position,
    ghost_brain,
    previous_action,
    decision_turn,
    danger_memory,
    training=True
):

    global pellet_detour_target
    global interrupted_navigation_target
    global navigation_target
    global navigation_path

    # ========================================================
    # 1. VALIDATE PHYSICAL MOVEMENT
    # ========================================================

    valid_actions = get_valid_actions(world)

    if not valid_actions:

        return None, "NO MOVES"

    # ========================================================
    # 2. IMMEDIATE GHOST DANGER
    # ========================================================

    if ghost_is_dangerous(
        vision
    ):

        # The old A* path may now be unsafe.
        # Keep its destination so we can resume later,
        # but force a fresh path after the danger response.
        navigation_path = None

        # ----------------------------------------------------
        # Emergency reflex
        # ----------------------------------------------------

        reflex = ghost_reflex_action(
            vision,
            valid_actions
        )

        if reflex is not None:

            return (
                reflex,
                "GHOST REFLEX"
            )

        # ----------------------------------------------------
        # Hard safety filter
        # ----------------------------------------------------

        safe_actions = get_ghost_safe_actions(
            vision,
            valid_actions
        )

        # ----------------------------------------------------
        # Ghost RL
        # ----------------------------------------------------

        action = ghost_brain.choose_action(
            vision,
            previous_action,
            training,
            allowed_actions=safe_actions,
            valid_actions=valid_actions
        )

        if action is not None:

            return (
                action,
                "GHOST RL"
            )

        # ----------------------------------------------------
        # Last resort
        # ----------------------------------------------------

        if safe_actions:

            return (
                random.choice(
                    safe_actions
                ),
                "GHOST SAFETY"
            )

        return (
            random.choice(
                valid_actions
            ),
            "GHOST LAST RESORT"
        )

    # ========================================================
    # 3. PELLET DETOUR
    # ========================================================

    # --------------------------------------------------------
    # Already collecting a pellet?
    # --------------------------------------------------------

    if pellet_detour_target is not None:

        path = astar_path(
            memory,
            pacman_position,
            pellet_detour_target,
            danger_memory,
            decision_turn
        )

        if (
            path is not None
            and len(path) >= 2
        ):

            action = direction_to_next(
                pacman_position,
                path[1]
            )

            if action is not None:

                return (
                    action,
                    "PELLET DETOUR"
                )

        # Pellet disappeared, was collected, or became
        # unreachable.  Return to normal navigation below.
        pellet_detour_target = None

    # --------------------------------------------------------
    # Look for a newly visible pellet.
    # --------------------------------------------------------

    if pellet_detour_target is None:

        visible_pellets = get_visible_pellets(
            vision,
            pacman_position
        )

        if visible_pellets:

            visible_pellets.sort(
                key=lambda item: item[1]
            )

            pellet_position, _ = (
                visible_pellets[0]
            )

            path = astar_path(
                memory,
                pacman_position,
                pellet_position,
                danger_memory,
                decision_turn
            )

            if (
                path is not None
                and len(path) >= 2
            ):

                # Remember the destination of normal navigation.
                #
                # Prefer the already selected persistent target.
                # If there isn't one yet, select one now.
                if (
                    navigation_target is not None
                    and navigation_target
                    != pellet_position
                ):

                    interrupted_navigation_target = (
                        navigation_target
                    )

                else:

                    interrupted_navigation_target = (
                        get_normal_navigation_target(
                            memory,
                            pacman_position,
                            danger_memory,
                            decision_turn
                        )
                    )

                pellet_detour_target = (
                    pellet_position
                )

                # The old normal path must not be followed
                # while collecting the pellet.
                navigation_path = None

                action = direction_to_next(
                    pacman_position,
                    path[1]
                )

                if action is not None:

                    return (
                        action,
                        "PELLET DETOUR"
                    )

                pellet_detour_target = None

    # ========================================================
    # 4. RESUME INTERRUPTED A* TARGET
    # ========================================================

    if (
        pellet_detour_target is None
        and interrupted_navigation_target is not None
    ):

        navigation_target = (
            interrupted_navigation_target
        )

        interrupted_navigation_target = None

        # Recalculate from Pac-Man's current position.
        navigation_path = None

        path = astar_path(
            memory,
            pacman_position,
            navigation_target,
            danger_memory,
            decision_turn,
            allow_danger_goal=(
                navigation_target
                == memory.find_exit()
            )
        )

        if (
            path is not None
            and len(path) >= 2
        ):

            navigation_path = path

            action = direction_to_next(
                pacman_position,
                path[1]
            )

            if action is not None:

                return (
                    action,
                    "RESUME A*"
                )

        # If the old target no longer works, normal navigation
        # will select/replan below.
        navigation_target = None
        navigation_path = None

    # ========================================================
    # 5. NORMAL MAP NAVIGATION
    # ========================================================

    action, mode = navigation_action(
        memory,
        pacman_position,
        danger_memory,
        decision_turn,
        prefer_exit=False
    )

    if action is not None:

        return action, mode

    # ========================================================
    # 6. EXIT FALLBACK
    # ========================================================

    action = get_exit_action(
        memory,
        pacman_position,
        danger_memory,
        decision_turn
    )

    if action is not None:

        return (
            action,
            "EXIT FALLBACK"
        )

    # ========================================================
    # 7. LAST RESORT
    # ========================================================

    if valid_actions:

        return (
            random.choice(
                valid_actions
            ),
            "RANDOM FALLBACK"
        )

    return None, "NO MOVES"


def run_training_episode(
    ghost_brain,
    episode
):

    ghost_brain.reset()

    global pellet_detour_target
    global interrupted_navigation_target
    global navigation_target
    global navigation_path

    pellet_detour_target = None
    interrupted_navigation_target = None
    navigation_target = None
    navigation_path = None

    maze = generate_maze()

    world = World(
        maze
    )

    sensor = CardinalSensor(
        world,
        max_range=SENSOR_RANGE
    )

    memory = MazeMemory()

    danger_memory = {}

    # Counts every action-selection attempt.  Unlike successful movement,
    # this clock cannot stall when an attempted move is rejected.
    decision_turn = 0
    steps = 0
    pellets_collected = 0
    cells_discovered = 0

    total_reward = 0.0

    previous_action = None

    outcome = "TIMEOUT"

    start_time = time.time()

    while decision_turn < MAX_TRAINING_STEPS:

        decision_turn += 1

        clear_screen()

        print(
            "========== PAC-BOT TRAINING ==========\n"
        )

        print(
            f"Episode: "
            f"{episode}/{TRAINING_EPISODES}"
        )

        print(
            f"Ghost Q-table states: "
            f"{len(ghost_brain.q_table)}"
        )

        print(
            f"Ghost exploration: "
            f"{ghost_brain.exploration_rate:.4f}"
        )

        print()

        display_world(
            world
        )

        print()

        print(
            "Position:",
            world.pacman_position
        )

        print(
            "Pellets remaining:",
            len(world.pellets)
        )

        print(
            "Decision attempts:",
            decision_turn,
            "/",
            MAX_TRAINING_STEPS
        )

        print(
            "Known cells:",
            memory.discovered
        )

        print(
            "Explored cells:",
            len(memory.explored)
        )

        print(
            "Frontiers:",
            len(memory.frontier_cells())
        )

        print(
            "Ghost danger cells:",
            len(danger_memory)
        )

        # ====================================================
        # SENSOR
        # ====================================================

        vision = sensor.scan()

        # ====================================================
        # GHOST MEMORY
        # ====================================================

        update_ghost_memory(
            vision,
            world.pacman_position,
            danger_memory,
            decision_turn
        )

        clean_ghost_memory(
            danger_memory,
            decision_turn
        )

        # ====================================================
        # MAP MEMORY
        # ====================================================

        _, new_cells = memory.update(
            vision,
            world.pacman_position
        )

        cells_discovered += new_cells

        exploration_reward = min(
            new_cells
            * NEW_CELL_REWARD,
            MAX_EXPLORATION_REWARD
        )

        # ====================================================
        # DECISION
        # ====================================================

        action, mode = decide_action(
            memory,
            vision,
            world,
            world.pacman_position,
            ghost_brain,
            previous_action,
            decision_turn,
            danger_memory,
            training=True
        )

        print(
            "Mode:",
            mode
        )

        print(
            "Action:",
            action
        )

        if action is None:

            outcome = "NO MOVES"

            break

        # Ghost RL is active only when
        # a ghost situation actually exists.
        ghost_situation = (
            mode == "GHOST RL"
            or mode == "GHOST REFLEX"
        )

        # Only this mode selected and registered an action in the Q brain.
        q_learning_action = mode == "GHOST RL"

        # ====================================================
        # MOVE PAC-MAN
        # ====================================================

        success, movement_reward, done = (
            world.move_pacman(
                action
            )
        )

        if success:

            steps += 1

            memory.record_visit(
                world.pacman_position
            )

            # Advance the cached A* path by the move we just made.
            # If the move was not the expected next path cell,
            # force a replan on the next decision.
            if (
                navigation_path is not None
                and len(navigation_path) >= 2
                and navigation_path[1]
                == world.pacman_position
            ):

                navigation_path = navigation_path[1:]

            else:

                navigation_path = None


        # ====================================================
        # PELLET DETOUR COMPLETION
        # ====================================================



        if (
            pellet_detour_target is not None
            and pellet_detour_target
            not in world.pellets
        ):

            # Pellet has been collected.
            #
            # Pellet collected.
            # The original A* target is preserved.

            pellet_detour_target = None
        # ====================================================
        # PELLET
        # ====================================================

        if movement_reward >= 10:

            pellets_collected += 1

        # ====================================================
        # MOVE GHOSTS
        # ====================================================

        world.move_ghosts()

        # ====================================================
        # COLLISION
        # ====================================================

        collision = (
            world.check_ghost_collision()
        )

        # ====================================================
        # REWARD
        # ====================================================

        reward = (
            movement_reward
            + exploration_reward
            + STEP_PENALTY
        )

        # Mild loop penalty.
        if (
            previous_action is not None
            and action == OPPOSITE[
                previous_action
            ]
        ):

            reward += (
                REVERSAL_PENALTY
            )

        # Small reward for correctly
        # reacting to ghost situations.
        if ghost_situation:

            reward += (
                GHOST_VISIBLE_REWARD
            )

        # ====================================================
        # DEATH
        # ====================================================

        if collision:

            reward += (
                GHOST_COLLISION_REWARD
            )

            if q_learning_action:

                ghost_brain.update(
                    reward,
                    sensor.scan(),
                    action,
                    done=True
                )

            total_reward += reward

            outcome = "DEATH"

            break

        # ====================================================
        # EXIT
        # ====================================================

        if done:

            if q_learning_action:

                ghost_brain.update(
                    reward,
                    sensor.scan(),
                    action,
                    done=True
                )

            total_reward += reward

            outcome = "VICTORY"

            break

        # ====================================================
        # GHOST Q-LEARNING
        # ====================================================

        if q_learning_action:

            next_vision = sensor.scan()

            ghost_brain.update(
                reward,
                next_vision,
                action,
                done=False,
                next_valid_actions=world.get_pacman_valid_actions()
            )

        total_reward += reward

        previous_action = action

        time.sleep(
            STEP_DELAY
        )

    # ========================================================
    # END EPISODE
    # ========================================================

    ghost_brain.decay_exploration()

    save_ghost_brain(
        ghost_brain
    )

    elapsed = (
        time.time()
        - start_time
    )

    clear_screen()

    print(
        "========================================"
    )

    print(
        f"Episode {episode}/{TRAINING_EPISODES}"
    )

    print(
        "========================================"
    )

    print(
        "Outcome:",
        outcome
    )

    print(
        f"Reward: {total_reward:.2f}"
    )

    print(
        f"Steps: {steps}"
    )

    print(
        f"Pellets collected: "
        f"{pellets_collected}"
    )

    print(
        f"Cells discovered: "
        f"{cells_discovered}"
    )

    print(
        f"Ghost Q-table states: "
        f"{len(ghost_brain.q_table)}"
    )

    print(
        f"Ghost exploration: "
        f"{ghost_brain.exploration_rate:.4f}"
    )

    print(
        f"Time: {elapsed:.2f}s"
    )

    time.sleep(1)


# ============================================================
# TEST
# ============================================================

def run_test(
    ghost_brain
):

    maze = generate_maze()

    world = World(
        maze
    )

    sensor = CardinalSensor(
        world,
        max_range=SENSOR_RANGE
    )

    memory = MazeMemory()

    danger_memory = {}

    old_exploration = (
        ghost_brain.exploration_rate
    )

    ghost_brain.exploration_rate = 0.0

    ghost_brain.reset()

    global pellet_detour_target
    global interrupted_navigation_target
    global navigation_target
    global navigation_path

    pellet_detour_target = None
    interrupted_navigation_target = None
    navigation_target = None
    navigation_path = None

    # Counts every action-selection attempt and is the test timeout clock.
    decision_turn = 0
    steps = 0

    previous_action = None

    start_time = time.time()

    outcome = "TIMEOUT"

    while decision_turn < MAX_TEST_STEPS:

        decision_turn += 1

        clear_screen()

        print(
            "========== PAC-BOT GREEDY TEST ==========\n"
        )

        print(
            "Q-learning exploration: 0.0"
        )

        print(
            f"Q-table states: "
            f"{len(ghost_brain.q_table)}"
        )

        print(
            f"Decision attempts: "
            f"{decision_turn}/{MAX_TEST_STEPS}"
        )

        print()

        display_world(
            world
        )

        print()

        print(
            "Position:",
            world.pacman_position
        )

        print(
            "Pellets remaining:",
            len(world.pellets)
        )

        print(
            "Known cells:",
            memory.discovered
        )

        print(
            "Explored cells:",
            len(memory.explored)
        )

        print(
            "Frontiers:",
            len(memory.frontier_cells())
        )

        print(
            "Ghost danger cells:",
            len(danger_memory)
        )

        # ====================================================
        # SENSOR
        # ====================================================

        vision = sensor.scan()

        # ====================================================
        # DEBUG LIVE GHOSTS
        # ====================================================

        live_ghosts = visible_ghost_positions(
            vision,
            world.pacman_position
        )

        if live_ghosts:

            print(
                "VISIBLE GHOSTS:",
                live_ghosts
            )

        # ====================================================
        # GHOST MEMORY
        # ====================================================

        update_ghost_memory(
            vision,
            world.pacman_position,
            danger_memory,
            decision_turn
        )

        clean_ghost_memory(
            danger_memory,
            decision_turn
        )

        # ====================================================
        # MAP
        # ====================================================

        memory.update(
            vision,
            world.pacman_position
        )

        # ====================================================
        # DECISION
        # ====================================================

        action, mode = decide_action(
            memory,
            vision,
            world,
            world.pacman_position,
            ghost_brain,
            previous_action,
            decision_turn,
            danger_memory,
            training=False
        )

        print(
            "Mode:",
            mode
        )

        print(
            "Action:",
            action
        )

        if action is None:

            print(
                "\nNO POSSIBLE MOVES!"
            )

            outcome = "NO MOVES"

            break

        # ====================================================
        # MOVE
        # ====================================================

        success, reward, done = (
            world.move_pacman(
                action
            )
        )

        if success:

            steps += 1

            memory.record_visit(
                world.pacman_position
            )

            # Advance the cached A* path by the move we just made.
            # If the move was not the expected next path cell,
            # force a replan on the next decision.
            if (
                navigation_path is not None
                and len(navigation_path) >= 2
                and navigation_path[1]
                == world.pacman_position
            ):

                navigation_path = navigation_path[1:]

            else:

                navigation_path = None

        # ====================================================
        # PELLET DETOUR COMPLETION
        # ====================================================

        if (
            pellet_detour_target is not None
            and pellet_detour_target not in world.pellets
        ):

            # Pellet has been collected.
            # The original A* target is preserved.

            pellet_detour_target = None

        # ====================================================
        # GHOSTS
        # ====================================================

        world.move_ghosts()

        # ====================================================
        # COLLISION
        # ====================================================

        if world.check_ghost_collision():

            elapsed = (
                time.time()
                - start_time
            )

            clear_screen()

            print(
                "========== PAC-BOT TEST ==========\n"
            )

            display_world(
                world
            )

            print()

            print(
                "💀 PAC-MAN WAS CAUGHT!"
            )

            print(
                f"Steps: {steps}"
            )

            print(
                f"Known cells: "
                f"{memory.discovered}"
            )

            print(
                f"Explored cells: "
                f"{len(memory.explored)}"
            )

            print(
                f"Time: {elapsed:.2f}s"
            )

            outcome = "DEATH"

            break

        # ====================================================
        # EXIT
        # ====================================================

        if done:

            elapsed = (
                time.time()
                - start_time
            )

            clear_screen()

            print(
                "========== PAC-BOT TEST ==========\n"
            )

            display_world(
                world
            )

            print()

            print(
                "🚪 PAC-MAN REACHED THE EXIT!"
            )

            print(
                f"Steps: {steps}"
            )

            print(
                f"Pellets remaining: "
                f"{len(world.pellets)}"
            )

            print(
                f"Known cells: "
                f"{memory.discovered}"
            )

            print(
                f"Explored cells: "
                f"{len(memory.explored)}"
            )

            print(
                f"Time: {elapsed:.2f}s"
            )

            outcome = "VICTORY"

            break

        previous_action = action

        time.sleep(
            STEP_DELAY
        )

    else:

        clear_screen()

        print(
            "========== PAC-BOT TEST ==========\n"
        )

        display_world(
            world
        )

        print()

        print(
            "⏱️ STEP LIMIT REACHED"
        )

        print(
            f"Known cells: "
            f"{memory.discovered}"
        )

        print(
            f"Explored cells: "
            f"{len(memory.explored)}"
        )

        outcome = "TIMEOUT"

    ghost_brain.exploration_rate = (
        old_exploration
    )

    print(
        f"\nFinal outcome: {outcome}"
    )

    time.sleep(2)


# ============================================================
# MAIN
# ============================================================

def main():

    ghost_brain = (
        GhostQLearningBrain()
    )

    load_ghost_brain(
        ghost_brain
    )

    # ========================================================
    # TRAIN
    # ========================================================

    for episode in range(
        1,
        TRAINING_EPISODES + 1
    ):

        run_training_episode(
            ghost_brain,
            episode
        )

    # ========================================================
    # TEST
    # ========================================================

    clear_screen()

    print(
        "========================================"
    )

    print(
        "       PAC-BOT TRAINING COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        f"Ghost Q-table states: "
        f"{len(ghost_brain.q_table)}"
    )

    print(
        f"Ghost exploration: "
        f"{ghost_brain.exploration_rate:.4f}"
    )

    print()

    print(
        "Starting greedy test..."
    )

    time.sleep(2)

    run_test(
        ghost_brain
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
