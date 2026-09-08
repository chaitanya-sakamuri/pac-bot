# 🟡 PacBot

> An intelligent Pac-Man agent that builds its own internal map, navigates using A*, explores unknown areas, reacts to ghosts, and learns ghost-avoidance behavior through Q-learning.

<img width="309" height="187" alt="pacbot" src="https://github.com/user-attachments/assets/c55b7ab7-5a4e-46fd-9ce0-3c751cd84d02" />


---

## 🧠 Overview

PacBot is an experimental AI agent built to explore how different forms of intelligence can work together inside a partially observable environment.

Instead of giving Pac-Man the complete maze, PacBot must discover the environment through a limited sensor, construct an internal representation of the world, decide where to go, navigate toward its objectives, and react when ghosts become dangerous.

The project combines:

- 🗺️ Internal world mapping
- 👁️ Limited-range perception
- 🧭 A* pathfinding
- 🔎 Autonomous exploration
- 🍒 Pellet-priority detours
- 👻 Ghost detection and danger memory
- 🤖 Q-learning for ghost avoidance
- 🛡️ Rule-based emergency reflexes

The goal is not simply to hard-code a route through a maze.

The goal is to create an agent that can:

**Perceive → Remember → Reason → Act → Learn**

---

## 🎥 Demo

<img width="309" height="187" alt="pacbot" src="https://github.com/user-attachments/assets/deecbc28-4d35-47d0-ab1e-8479775443af" />

PacBot explores a procedurally generated maze while maintaining an internal representation of the environment and reacting to dynamically moving ghosts.

---

# 🧠 How PacBot Thinks

PacBot does not receive the complete maze directly.

Its decision process is approximately:

```text
                ┌─────────────────┐
                │      WORLD      │
                │ Maze + Pellets  │
                │    + Ghosts     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │     SENSOR      │
                │ Limited vision  │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  INTERNAL MAP   │
                │   MazeMemory    │
                └────────┬────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Normal Navigation       Ghost Detection
              │                     │
              ▼                     ▼
             A*              Reflex / Q-Learning
              │                     │
              └──────────┬──────────┘
                         │
                         ▼
                       ACTION
````

---

# 🗺️ Internal Map

One of the main ideas behind PacBot is that the agent maintains its own **internal map of the maze**.

The real world contains information that PacBot has not necessarily discovered yet.

Its memory records things such as:

* Known walls
* Known walkable cells
* Visited cells
* Pellets
* Exit
* Exploration frontiers

Unknown areas remain unknown until the sensor discovers them.

Conceptually:

```text
Real World

#####################
#.......#...........#
#.#####.#.#########.#
#.....#.#.......#...#
#####.#.#######.#.###
#.....#.........#...#
#####################


PacBot's Internal Map

#####################
#.......#...........?
#.#####.#.#########??
#.....#.#.......#????
#####.#.#######.?????
#.....#.........??????
#####################?
```

As PacBot moves, the internal map becomes increasingly complete.

This allows the agent to reason about places it has already discovered instead of relying only on its current visual input.

---

# 👁️ Limited Perception

PacBot uses a cardinal sensor that looks in the four directions:

```text
             UP
              ↑
              │
        ←──── P ────→
              │
              ↓
            DOWN
```

The sensor has a limited range and stops when it encounters a wall.

This creates a simple **partial-observability** environment.

PacBot therefore has to combine:

```text
Current perception
        +
Previous observations
        ↓
Internal world model
```

rather than simply reading the entire maze.

---

# 🧭 A* Navigation

Once PacBot knows where it wants to go, it uses **A*** to find a route through its known map.

A* combines:

```text
f(n) = g(n) + h(n)
```

where:

* `g(n)` = cost from the current position
* `h(n)` = estimated cost to the destination

A* is used for:

* Reaching the known exit
* Exploring selected frontier cells
* Reaching visible pellets
* Resuming interrupted navigation

The important distinction is that A* operates on **PacBot's internal knowledge**, rather than magically knowing undiscovered parts of the maze.

---

# 🔎 Autonomous Exploration

If the exit is not known, PacBot looks for **frontier cells**.

A frontier is an area where the known map meets unexplored territory.

For example:

```text
###########
#.........#
#.........#
#.....????#
#.....????#
###########
       ↑
    frontier
```

PacBot evaluates possible exploration targets using factors such as:

* Distance
* Number of unknown neighboring cells
* Previous visits
* Reachability under current danger constraints

It then selects a useful frontier and navigates toward it using A*.

This creates a continuous exploration loop:

```text
Explore
   ↓
Discover
   ↓
Update internal map
   ↓
Choose new frontier
   ↓
A*
   ↓
Explore again
```

---

# 🍒 Pellet Priority

When PacBot detects a pellet within its sensor range, it can temporarily interrupt its current navigation objective.

The process is:

```text
Normal A* navigation
        ↓
Pellet detected
        ↓
Save current destination
        ↓
A* → Pellet
        ↓
Collect pellet
        ↓
Resume previous objective
```

This allows pellets to act as opportunistic targets without permanently destroying the main navigation plan.

---

# 👻 Ghost Avoidance

Ghosts are treated differently from the static maze.

They are dynamic objects and therefore are not permanently stored as part of the static internal map.

Instead, PacBot maintains temporary **danger memory** around recently observed ghosts.

When a ghost becomes dangerous, normal navigation can be interrupted.

The current decision hierarchy includes:

```text
Ghost danger
    │
    ├── Emergency reflex
    │
    ├── Safety filtering
    │
    └── Q-learning
```

Immediate safety takes priority over normal exploration.

---

# 🤖 Q-Learning

PacBot uses a Q-learning system specifically for **ghost-avoidance decisions**.

The Q-table stores estimated values for:

```text
(state, action) → expected future reward
```

Over repeated training episodes, the agent learns which actions tend to produce better outcomes in dangerous situations.

A simplified learning loop is:

```text
Observe state
     ↓
Choose action
     ↓
Move
     ↓
Receive reward
     ↓
Observe next state
     ↓
Update Q-value
```

The Q-learning component does not control the entire Pac-Man brain.

Instead, it is one component inside the larger decision system.

This allows deterministic algorithms such as A* to handle navigation while reinforcement learning handles a more dynamic problem:

**How should PacBot react when ghosts become dangerous?**

---

# 🔀 Hybrid Intelligence

PacBot intentionally combines several approaches rather than forcing one algorithm to solve everything.

| Component            | Responsibility               |
| -------------------- | ---------------------------- |
| Sensor               | Perception                   |
| MazeMemory           | Internal world model         |
| A*                   | Navigation                   |
| Frontier exploration | Discovering unknown areas    |
| Pellet system        | Opportunistic objectives     |
| Danger memory        | Temporary ghost knowledge    |
| Rule-based reflex    | Immediate emergency response |
| Q-learning           | Learned ghost avoidance      |
| World                | Environment simulation       |

The philosophy is:

> **Use rules where the problem is deterministic, search where planning is useful, and learning where behavior benefits from experience.**

---

# 🧪 Training

PacBot can train its ghost-avoidance behavior over multiple procedurally generated episodes.

Each episode generates a new environment and allows the Q-learning component to experience different situations.

A typical training process looks like:

```text
Generate maze
     ↓
Initialize world
     ↓
Explore / navigate
     ↓
Encounter ghosts
     ↓
Learn from decisions
     ↓
Update Q-table
     ↓
Repeat
```

The learned Q-table is persisted to:

```text
ghost_qtable.pkl
```

After training, PacBot can be evaluated using a greedy policy with exploration disabled.

---

# 🧪 Greedy Evaluation

During evaluation, the learned policy can be tested with:

```text
ε = 0
```

This disables intentional exploration by the Q-learning agent.

Greedy evaluation helps determine what behavior the learned Q-table has actually acquired.

The evaluation can also use a newly generated maze to test how well the learned behavior generalizes.

---

# 🏗️ Project Structure

```text
pacbot/
│
├── main.py
│       Main controller, decision system,
│       A* navigation, exploration and
│       training/testing loops.
│
├── maze.py
│       Procedural maze generation.
│
├── maze_memory.py
│       PacBot's internal representation
│       of the discovered maze.
│
├── sensor.py
│       Limited-range cardinal perception.
│
├── world.py
│       Environment simulation, Pac-Man,
│       pellets and ghosts.
│
├── ghost_qbrain.py
│       Q-learning brain used for
│       ghost avoidance.
│
├── brain.py
│       Legacy rule-based controller.
│
├── ghost_qtable.pkl
│       Persisted learned Q-table.
│
├── assets/
│   └── pacbot.gif
│       Demo animation.
│
└── README.md
```

---

# ⚙️ Architecture

The current system follows this general decision flow:

```text
                 ┌───────────────┐
                 │   Perception  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │ Internal Map  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │ Ghost Danger? │
                 └───────┬───────┘
                     YES │ NO
                         │
          ┌──────────────┘
          ↓
   Ghost avoidance
          │
          ↓
   Pellet detected?
          │
          ↓
   Pellet detour
          │
          ↓
    Normal A*
          │
          ↓
     Exploration
```

The system is intentionally modular so individual components can be improved independently.

---

# 📊 Why This Project Is Interesting

PacBot is not simply a Pac-Man implementation with an A* solver.

The agent has to deal with several different problems at once:

### Perception

It only sees a limited portion of the environment.

### Memory

It must remember what it has already discovered.

### Planning

It needs to navigate toward useful destinations.

### Exploration

It needs to decide where to investigate next.

### Dynamic threats

Ghosts can change the safety of previously valid routes.

### Learning

Some decisions are learned through repeated experience rather than explicitly programmed.

This makes PacBot a small experimental platform for studying **agent architecture**.

---

# 🚀 Future Goals

The long-term goal is to evolve PacBot into a more capable experimental AI agent.

Potential improvements include:

* 🧠 Better Q-learning state representation
* 👻 Predictive ghost movement
* 🗺️ More sophisticated world modeling
* 🔎 Improved exploration strategies
* ⚡ More efficient A* implementation
* 🛣️ Better route-cost functions
* 📍 More stable navigation targets
* 📈 Training statistics and performance graphs
* 👁️ Visualization of PacBot's internal beliefs
* 🧪 Large-scale evaluation across unseen mazes
* 🤖 More advanced reinforcement-learning approaches

---

# 🛠️ Running the Project

Clone the repository:

```bash
git clone <your-repository-url>
cd pacbot
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Run PacBot:

```bash
python3 main.py
```

Training and testing behavior can be configured through the settings in `main.py`.

---

# 🧰 Technologies

* Python
* A* pathfinding
* Q-learning
* Procedural maze generation
* Reinforcement learning
* Grid-based simulation
* Partial observability
* Internal world modeling

---

# 📌 Project Philosophy

PacBot is an experiment in combining **classical algorithms with learning**.

Rather than asking:

> "Can a neural network learn to play Pac-Man?"

the project asks:

> **"How capable can a small agent become when perception, memory, planning, rules, and learning are combined?"**

The interesting part isn't simply whether PacBot reaches the exit.

It's watching an agent build an understanding of its environment and use that understanding to make increasingly intelligent decisions.

---

# 👤 Author

**Chaitanya**

Engineering student exploring AI, algorithms, reinforcement learning, and intelligent agents.

---

# ⭐ Future Vision

The ultimate goal is to evolve PacBot from a game-playing program into a compact experimental AI architecture:

```text
PERCEIVE
   ↓
REMEMBER
   ↓
UNDERSTAND
   ↓
PLAN
   ↓
ACT
   ↓
LEARN
   ↺
```

And eventually:

> **Give it a world it has never seen and see what it can figure out.**

```
```
