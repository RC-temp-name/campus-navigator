# campus-navigator

> **A web app that gives step-by-step walking directions inside a university building.** Think Google Maps, but for hallways and staircases.

---

## What Are We Building?

Picture this: it's the first day of university. You found the right building, but you have no idea how to get to your classroom. You open our website, type in your classroom number and the building you're already in, and the app walks you through it step by step:

> _"Walk through the double doors. → Turn left at the staircase. → Your classroom is the second door on your right."_

Each instruction can be dismissed as you go, similar to how Google Maps lets you skip a step once you've completed it. The first version covers **one building**. The project is designed so it can grow later.

---

## Tech Stack

|Tool|What It Does|
|---|---|
|**Python**|Main programming language for backend logic|
|**Flask**|Turns our Python code into a running website|
|**NetworkX**|Models the building as a graph and calculates the shortest path between rooms|
|**HTML & CSS**|Structure and styling of the webpage|
|**SVG / Leaflet.js**|Draws the animated blue route line over the floor plan image|
|**JSON**|Text files that store our building data (rooms, coordinates, connections)|
|**uv**|Package manager — installs and manages Python libraries|
|**Git**|Version control — tracks changes so the team can collaborate without overwriting each other|

### How the Pathfinding Works

The building is modeled as a **graph** — locations are **nodes** and the walking paths between them are **edges**. Every node stores two things:

1. A text instruction (e.g., `"Turn left at the staircase"`)
2. Pixel coordinates on the floor plan image (e.g., `x=300, y=150`)

When a user asks for directions, `NetworkX` runs a shortest-path algorithm across the graph and returns a list of nodes. From that one list, we produce both the step-by-step text directions _and_ the visual blue line — the coordinates are already stored in the nodes.

---

## Project Structure

```
campus_navigator/
│
├── run.py                       ← Start the app by running this file
├── requirements.txt             ← List of all Python libraries the project needs
├── README.md                    ← This file
│
├── app/                         ← Everything that makes the app work lives here
│   ├── __init__.py              ← Tells Python "this folder is a package" & starts Flask
│   ├── routes.py                ← Handles URLs: connects user input → logic → webpage
│   │
│   ├── logic/                   ← The "brain" of the app (pathfinding code)
│   │   ├── __init__.py
│   │   └── graph_manager.py     ← Loads building data, runs NetworkX, returns directions
│   │
│   ├── static/                  ← Files the browser downloads directly
│   │   ├── css/
│   │   │   └── style.css        ← Page styling
│   │   ├── js/
│   │   │   └── map.js           ← Draws the blue route line (Leaflet.js logic)
│   │   └── img/
│   │       └── floorplan.png    ← The floor plan image displayed on screen
│   │
│   └── templates/               ← HTML pages Flask serves to the user
│       ├── base.html            ← Shared page skeleton (nav bar, footer, etc.)
│       └── index.html           ← The main search + map page
│
└── data/                        ← Building data — treated like a database
    ├── nodes.json               ← Every room/intersection with its name and coordinates
    └── edges.json               ← Every walking connection between two nodes
```

This structure follows the **MVC (Model–View–Controller)** pattern — each part of the app has one job and they don't mix. The practical benefit for the team is that multiple people can work on different files simultaneously without conflicting.

- **`data/`** — raw building data. Can be edited without touching any Python.
- **`app/logic/`** — pure pathfinding logic. Can be tested without running the website.
- **`app/templates/` and `app/static/`** — everything the user sees. No math here.
- **`app/routes.py`** — connects the other three. No math, no styling.

---

## How the Code Connects

```
User types "Room 101" and clicks Go
        ↓
routes.py receives the form input
        ↓
routes.py calls graph_manager.py with (start="Entrance", end="Room 101")
        ↓
graph_manager.py loads nodes.json and edges.json
graph_manager.py runs NetworkX shortest_path()
graph_manager.py returns: text directions + pixel coordinates
        ↓
routes.py passes results to index.html (via Flask's render_template)
        ↓
index.html displays the step-by-step text directions
map.js reads the coordinates and draws the blue line over floorplan.png
        ↓
User sees directions on screen ✓
```

---

## Team Roles

Roles can be shared — it's fine for two people to work in the same area. What matters is that everyone knows which files they own so we don't overwrite each other. If you need to touch a file outside your area, give the owner a heads up first.

### 🗂️ Data (1–2 people)

**Workspace: `data/`**

Walk the building and define the graph. Every intersection, staircase, entrance, and classroom becomes a node. Record the pixel coordinates for each by opening the floor plan image and hovering over each location to find its X/Y position. Deliverables are `nodes.json` and `edges.json` — the rest of the app depends on this data.

### ⚙️ Backend (1–2 people)

**Workspace: `app/logic/graph_manager.py`**

Write the Python function that loads the JSON files, builds the NetworkX graph, and returns both text directions and the coordinate list for the route. This can be built and tested as a standalone Python script — no webpage needed.

### 🎨 Frontend (1–2 people)

**Workspace: `app/templates/`, `app/static/`**

Build the HTML/CSS pages and write the JavaScript (`map.js`) that draws the animated blue line over the floor plan. Keep it mobile-friendly — users will be on their phones while walking.

### 🔌 Integration (1 person)

**Workspace: `app/__init__.py`, `app/routes.py`, `run.py`**

Set up Flask and write the routes that connect the backend functions to the frontend pages. Make sure that when the form submits, the right code runs and the result shows up on screen.

---

## Git Basics

> **Git and GitHub are different things.**
> 
> - **Git** is a tool on your computer that tracks changes to files.
> - **GitHub** is a website that hosts a shared copy of the project online.

### Every Work Session

```bash
# Before you start — get your teammates' latest changes
git pull

# After finishing a chunk of work
git add .
git commit -m "describe what you did"
git push
```

### The Rules

1. **Never commit directly to `main`.** Work on your own branch and let the team leader merge it.
2. **Pull before you push.** Always `git pull` before `git push`.
3. **Write descriptive commit messages.** `"fixed stuff"` is not useful. `"Fixed bug when start and end room are the same"` is.
4. **Respect each other's files.** Communicate before editing outside your workspace.

---

## Setting Up Your Environment

> For **Windows** users — follow these steps in order.

### Step 1 — Install VSCode

Download from [https://code.visualstudio.com](https://code.visualstudio.com/). Install the **Python extension** from the Extensions tab on the left sidebar.

### Step 2 — Install Python

Download from [https://www.python.org/downloads/](https://www.python.org/downloads/). During installation, **check "Add Python to PATH"** — easy to miss, important to do.

### Step 3 — Install uv

Open the terminal in VSCode (`` Ctrl + ` ``) and run:

```bash
pip install uv
```

### Step 4 — Clone the Repository

```bash
git clone https://github.com/[our-repo-link-here]
cd campus_navigator
```

### Step 5 — Install Dependencies

```bash
uv sync
```

### Step 6 — Run the App

_(not set up yet — will update this when the server is ready)_

---

## TODO — First Week

- [ ] **Learn how to use `uv` package manager** — [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- [ ] **Learn how to use VSCode**
- [ ] **Learn Python** — [freecodecamp.org](https://www.freecodecamp.org/)
- [ ] **Learn how Git works** — [git branching game](https://learngitbranching.js.org/?locale=en_US)

> **Note:** Git and GitHub are different. Focus on understanding `clone`, `add`, `commit`, `push`, and `pull` — those five commands cover 90% of what we'll use.
