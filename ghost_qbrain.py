import os
import pickle
import random


class GhostQLearningBrain:

    ACTIONS = [
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT"
    ]

    OPPOSITE = {
        "UP": "DOWN",
        "DOWN": "UP",
        "LEFT": "RIGHT",
        "RIGHT": "LEFT"
    }

    def __init__(
        self,
        learning_rate=0.15,
        discount_factor=0.90,
        exploration_rate=1.0,
        exploration_min=0.05,
        exploration_decay=0.995
    ):

        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

        self.exploration_rate = exploration_rate
        self.exploration_min = exploration_min
        self.exploration_decay = exploration_decay

        self.q_table = {}

        self.last_state = None
        self.last_action = None

    # ==================================================
    # STATE
    # ==================================================

    def get_state(
        self,
        vision,
        previous_action=None
    ):
        """
        The Q-table only learns ghost-related situations.

        State contains:

        1. Ghost distance in each direction
        2. Immediate walls
        3. Previous action

        Ghost distance buckets:

            0 = no visible ghost
            1 = adjacent
            2 = distance 2-3
            3 = distance 4-5
            4 = distance 6+

        Importantly, the sensor already stops at walls.
        """

        state = []

        directions = [
            "UP",
            "DOWN",
            "LEFT",
            "RIGHT"
        ]

        # --------------------------------------------------
        # GHOST DISTANCE
        # --------------------------------------------------

        for direction in directions:

            cells = vision.get(
                direction,
                []
            )

            ghost_bucket = 0

            for distance, cell in enumerate(
                cells,
                start=1
            ):

                if cell == "G":

                    if distance == 1:
                        ghost_bucket = 1

                    elif distance <= 3:
                        ghost_bucket = 2

                    elif distance <= 5:
                        ghost_bucket = 3

                    else:
                        ghost_bucket = 4

                    break

                if cell == "#":
                    break

            state.append(ghost_bucket)

        # --------------------------------------------------
        # IMMEDIATE WALLS
        # --------------------------------------------------

        for direction in directions:

            cells = vision.get(
                direction,
                []
            )

            if not cells:
                state.append(1)

            else:
                state.append(
                    1
                    if cells[0] == "#"
                    else 0
                )

        # --------------------------------------------------
        # PREVIOUS ACTION
        # --------------------------------------------------

        action_encoding = {
            None: 0,
            "UP": 1,
            "DOWN": 2,
            "LEFT": 3,
            "RIGHT": 4
        }

        state.append(
            action_encoding.get(
                previous_action,
                0
            )
        )

        return tuple(state)

    # ==================================================
    # Q VALUES
    # ==================================================

    def get_q_values(self, state):

        if state not in self.q_table:

            self.q_table[state] = {
                action: 0.0
                for action in self.ACTIONS
            }

        return self.q_table[state]

    # ==================================================
    # VALID ACTIONS
    # ==================================================

    def get_valid_actions(self, vision):

        valid_actions = []

        for direction in self.ACTIONS:

            cells = vision.get(
                direction,
                []
            )

            if not cells:
                continue

            if cells[0] == "#":
                continue

            valid_actions.append(direction)

        return valid_actions

    # ==================================================
    # GHOST DISTANCE
    # ==================================================

    def ghost_distance(
        self,
        vision,
        direction
    ):

        cells = vision.get(
            direction,
            []
        )

        for distance, cell in enumerate(
            cells,
            start=1
        ):

            if cell == "G":
                return distance

            if cell == "#":
                break

        return None

    # ==================================================
    # VISIBLE GHOST DIRECTIONS
    # ==================================================

    def visible_ghost_directions(
        self,
        vision
    ):

        dangerous = []

        for direction in self.ACTIONS:

            distance = self.ghost_distance(
                vision,
                direction
            )

            if distance is not None:
                dangerous.append(direction)

        return dangerous

    # ==================================================
    # HARD SAFETY RULE
    # ==================================================

    def get_safe_actions(
        self,
        vision,
        valid_actions
    ):
        """
        HARD RULE:

        If Pac-Man can see a ghost in a direction,
        he cannot deliberately move toward that ghost.

        Q-learning is NOT allowed to override this.
        """

        ghost_directions = (
            self.visible_ghost_directions(
                vision
            )
        )

        safe_actions = [
            action
            for action in valid_actions
            if action not in ghost_directions
        ]

        return safe_actions

    # ==================================================
    # EMERGENCY REFLEX
    # ==================================================

    def emergency_reflex(
        self,
        vision,
        valid_actions
    ):
        """
        Handles immediate ghost danger.

        If a ghost is directly adjacent,
        choose an available direction that does
        NOT contain a visible ghost.

        If there are multiple possible escapes,
        return None and allow Q-learning/navigation
        to decide between them.
        """

        adjacent_ghosts = []

        for direction in self.ACTIONS:

            distance = self.ghost_distance(
                vision,
                direction
            )

            if distance == 1:
                adjacent_ghosts.append(
                    direction
                )

        if not adjacent_ghosts:
            return None

        safe_actions = [
            action
            for action in valid_actions
            if action not in adjacent_ghosts
        ]

        if not safe_actions:
            return None

        # If only one escape exists,
        # take it immediately.
        if len(safe_actions) == 1:
            return safe_actions[0]

        # Multiple escapes:
        # let the higher-level decision system choose.
        return None

    # ==================================================
    # CHOOSE ACTION
    # ==================================================

    def choose_action(
        self,
        vision,
        previous_action=None,
        training=True,
        allowed_actions=None,
        valid_actions=None
    ):

        state = self.get_state(
            vision,
            previous_action
        )

        # --------------------------------------------------
        # PHYSICALLY VALID ACTIONS
        # --------------------------------------------------

        # The caller supplies the world's authoritative legal-action mask so
        # Q-learning cannot choose a ghost-occupied cell merely because the
        # sensor reports an open corridor.
        if valid_actions is None:
            valid_actions = self.get_valid_actions(vision)
        else:
            valid_actions = list(valid_actions)

        if not valid_actions:

            self.last_state = state
            self.last_action = None

            return None

        # --------------------------------------------------
        # HARD GHOST SAFETY
        # --------------------------------------------------

        safe_actions = self.get_safe_actions(
            vision,
            valid_actions
        )

        # --------------------------------------------------
        # EXTERNAL SAFETY / NAVIGATION FILTER
        # --------------------------------------------------

        if allowed_actions is not None:

            allowed_actions = set(
                allowed_actions
            )

            filtered = [
                action
                for action in safe_actions
                if action in allowed_actions
            ]

            if filtered:
                safe_actions = filtered

        # --------------------------------------------------
        # EMERGENCY REFLEX
        # --------------------------------------------------

        reflex_action = self.emergency_reflex(
            vision,
            valid_actions
        )

        if reflex_action is not None:

            if (
                not safe_actions
                or reflex_action in safe_actions
            ):

                self.last_state = state
                self.last_action = reflex_action

                return reflex_action

        # --------------------------------------------------
        # IF ALL SAFE ACTIONS DISAPPEARED
        # --------------------------------------------------

        if not safe_actions:

            # This means every available movement
            # is currently toward a visible ghost.

            # We cannot avoid everything.
            # Choose from physically valid actions.
            safe_actions = valid_actions

        # --------------------------------------------------
        # Q VALUES
        # --------------------------------------------------

        q_values = self.get_q_values(
            state
        )

        # --------------------------------------------------
        # EXPLORATION
        # --------------------------------------------------

        if (
            training
            and random.random()
            < self.exploration_rate
        ):

            action = random.choice(
                safe_actions
            )

        # --------------------------------------------------
        # EXPLOITATION
        # --------------------------------------------------

        else:

            best_value = max(
                q_values[action]
                for action in safe_actions
            )

            best_actions = [
                action
                for action in safe_actions
                if q_values[action] == best_value
            ]

            # Random tie-breaking prevents
            # deterministic oscillation when
            # Q-values are identical.
            action = random.choice(
                best_actions
            )

        # --------------------------------------------------
        # REMEMBER
        # --------------------------------------------------

        self.last_state = state
        self.last_action = action

        return action

    # ==================================================
    # Q-LEARNING UPDATE
    # ==================================================

    def update(
        self,
        reward,
        next_vision=None,
        next_previous_action=None,
        done=False,
        next_valid_actions=None
    ):

        if self.last_state is None:
            return

        if self.last_action is None:
            return

        current_q = self.get_q_values(
            self.last_state
        )[self.last_action]

        # --------------------------------------------------
        # TERMINAL STATE
        # --------------------------------------------------

        if done:

            target = reward

        else:

            next_state = self.get_state(
                next_vision,
                next_previous_action
            )

            if next_valid_actions is None:
                next_valid_actions = self.get_valid_actions(next_vision)
            else:
                next_valid_actions = list(next_valid_actions)

            # Apply the same ghost safety rule
            # while evaluating future actions.
            next_safe_actions = (
                self.get_safe_actions(
                    next_vision,
                    next_valid_actions
                )
            )

            if next_safe_actions:

                next_q_values = (
                    self.get_q_values(
                        next_state
                    )
                )

                best_next_q = max(
                    next_q_values[action]
                    for action in next_safe_actions
                )

            elif next_valid_actions:

                next_q_values = (
                    self.get_q_values(
                        next_state
                    )
                )

                best_next_q = max(
                    next_q_values[action]
                    for action in next_valid_actions
                )

            else:

                best_next_q = 0.0

            target = (
                reward
                + self.discount_factor
                * best_next_q
            )

        # --------------------------------------------------
        # UPDATE
        # --------------------------------------------------

        self.q_table[
            self.last_state
        ][self.last_action] += (
            self.learning_rate
            * (
                target
                - current_q
            )
        )

    # ==================================================
    # EXPLORATION DECAY
    # ==================================================

    def decay_exploration(self):

        self.exploration_rate = max(
            self.exploration_min,
            self.exploration_rate
            * self.exploration_decay
        )

    # ==================================================
    # RESET EPISODE MEMORY
    # ==================================================

    def reset(self):

        self.last_state = None
        self.last_action = None

    # ==================================================
    # SAVE
    # ==================================================

    def save(
        self,
        filename="ghost_qtable.pkl"
    ):

        data = {
            "q_table": self.q_table,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "exploration_rate": self.exploration_rate,
            "exploration_min": self.exploration_min,
            "exploration_decay": self.exploration_decay
        }

        with open(
            filename,
            "wb"
        ) as file:

            pickle.dump(
                data,
                file
            )

    # ==================================================
    # LOAD
    # ==================================================

    def load(
        self,
        filename="ghost_qtable.pkl"
    ):

        if not os.path.exists(
            filename
        ):
            return False

        with open(
            filename,
            "rb"
        ) as file:

            data = pickle.load(file)

        self.q_table = data.get(
            "q_table",
            {}
        )

        self.learning_rate = data.get(
            "learning_rate",
            self.learning_rate
        )

        self.discount_factor = data.get(
            "discount_factor",
            self.discount_factor
        )

        self.exploration_rate = data.get(
            "exploration_rate",
            self.exploration_rate
        )

        self.exploration_min = data.get(
            "exploration_min",
            self.exploration_min
        )

        self.exploration_decay = data.get(
            "exploration_decay",
            self.exploration_decay
        )

        return True

    # ==================================================
    # Q-TABLE SIZE
    # ==================================================

    def state_count(self):

        return len(
            self.q_table
        )
