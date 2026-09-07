import json

import networkx as nx
import pytest

from app import logic
from app.logic import graph_manager as manager


@pytest.fixture(autouse=True)
def reset_global_graph():
    manager.G = None
    yield
    manager.G = None


def configure_data_root(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    logic_path = repo_root / "app" / "logic"
    data_path = repo_root / "data"
    logic_path.mkdir(parents=True)
    data_path.mkdir()
    monkeypatch.setattr(manager, "__file__", str(logic_path / "graph_manager.py"))
    return data_path


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def make_graph(*nodes, edges=()):
    graph = nx.DiGraph()
    for node_id, attributes in nodes:
        graph.add_node(node_id, **attributes)
    for source, target, attributes in edges:
        graph.add_edge(source, target, **attributes)
    return graph


def node(floor=1, node_type="waypoint", x=0, y=0, name="Node"):
    return {"floor": floor, "type": node_type, "coords": [x, y], "name": name}


def test_read_json_files_loads_nodes_and_edges(monkeypatch, tmp_path):
    data_path = configure_data_root(monkeypatch, tmp_path)
    nodes = [{"id": "a", "type": "room"}]
    edges = [{"source": "a", "target": "a", "weight": 0}]
    write_json(data_path / "nodes.json", nodes)
    write_json(data_path / "edges.json", edges)

    assert manager.read_json_files() == (nodes, edges)


@pytest.mark.parametrize(
    ("missing_file", "message"),
    [
        ("nodes.json", "Failed to load nodes data"),
        ("edges.json", "Failed to load edges data"),
    ],
)
def test_read_json_files_reports_missing_data(
    monkeypatch, tmp_path, missing_file, message
):
    data_path = configure_data_root(monkeypatch, tmp_path)
    write_json(data_path / "nodes.json", [])
    write_json(data_path / "edges.json", [])
    (data_path / missing_file).unlink()

    with pytest.raises(RuntimeError, match=message):
        manager.read_json_files()


@pytest.mark.parametrize(
    ("invalid_file", "message"),
    [
        ("nodes.json", "Failed to load nodes data"),
        ("edges.json", "Failed to load edges data"),
    ],
)
def test_read_json_files_reports_invalid_json(
    monkeypatch, tmp_path, invalid_file, message
):
    data_path = configure_data_root(monkeypatch, tmp_path)
    write_json(data_path / "nodes.json", [])
    write_json(data_path / "edges.json", [])
    (data_path / invalid_file).write_text("not json", encoding="utf-8")

    with pytest.raises(RuntimeError, match=message):
        manager.read_json_files()


def test_read_json_files_uses_module_path_instead_of_working_directory(
    monkeypatch, tmp_path
):
    data_path = configure_data_root(monkeypatch, tmp_path)
    nodes = [{"id": "from-module-path"}]
    edges = [{"source": "from-module-path", "target": "from-module-path"}]
    write_json(data_path / "nodes.json", nodes)
    write_json(data_path / "edges.json", edges)
    other_directory = tmp_path / "unrelated-working-directory"
    other_directory.mkdir()
    monkeypatch.chdir(other_directory)

    assert manager.read_json_files() == (nodes, edges)


def test_build_graph_preserves_node_and_edge_data(monkeypatch):
    nodes = [
        {"id": "a", "name": "A", "floor": 1},
        {"id": "b", "name": "B", "floor": 2},
    ]
    edges = [{"source": "a", "target": "b", "weight": 4, "instruction": "Go up."}]
    monkeypatch.setattr(manager, "read_json_files", lambda: (nodes, edges))

    graph = manager.build_graph()

    assert isinstance(graph, nx.DiGraph)
    assert graph.nodes["a"] == nodes[0]
    assert graph["a"]["b"] == edges[0]
    assert not graph.has_edge("b", "a")


def test_reload_graph_replaces_cached_graph(monkeypatch):
    graph = nx.DiGraph()
    monkeypatch.setattr(manager, "build_graph", lambda: graph)

    manager.reload_graph()

    assert manager.G is graph


def test_shortest_route_uses_edge_weights_and_handles_missing_routes():
    graph = nx.DiGraph()
    graph.add_weighted_edges_from(
        [("start", "direct", 10), ("start", "detour", 2), ("detour", "direct", 3)]
    )

    assert manager.shortest_route(graph, "start", "direct") == [
        "start",
        "detour",
        "direct",
    ]
    assert manager.shortest_route(graph, "direct", "start") is None
    assert manager.shortest_route(graph, "unknown", "start") is None


def test_shortest_route_returns_the_start_node_for_same_node_routes():
    graph = nx.DiGraph()
    graph.add_node("room")

    assert manager.shortest_route(graph, "room", "room") == ["room"]


def test_get_floor_bounds_reads_dimensions(monkeypatch, tmp_path):
    data_path = configure_data_root(monkeypatch, tmp_path)
    write_json(
        data_path / "floors.json",
        {"BLDG": {"2": {"width_feet": 120, "height_feet": 80}}},
    )

    assert manager.get_floor_bounds("BLDG", 2) == {"width": 120, "height": 80}


@pytest.mark.parametrize(
    ("floors_data", "building", "floor", "message"),
    [
        ({"BLDG": {}}, "BLDG", 2, "No floor data for BLDG floor 2"),
        ({}, "BLDG", 2, "No floor data for BLDG floor 2"),
    ],
)
def test_get_floor_bounds_rejects_unknown_floor(
    monkeypatch, tmp_path, floors_data, building, floor, message
):
    data_path = configure_data_root(monkeypatch, tmp_path)
    write_json(data_path / "floors.json", floors_data)

    with pytest.raises(RuntimeError, match=message):
        manager.get_floor_bounds(building, floor)


def test_get_floor_bounds_reports_invalid_json(monkeypatch, tmp_path):
    data_path = configure_data_root(monkeypatch, tmp_path)
    (data_path / "floors.json").write_text("not json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Failed to load floors data"):
        manager.get_floor_bounds("BLDG", 1)


def test_get_floor_bounds_reports_missing_file(monkeypatch, tmp_path):
    configure_data_root(monkeypatch, tmp_path)

    with pytest.raises(RuntimeError, match="Failed to load floors data"):
        manager.get_floor_bounds("BLDG", 1)


def test_get_options_separates_connectors_and_rooms(monkeypatch):
    nodes = [
        {"id": "e", "name": "Elevator", "type": "elevator"},
        {"id": "s", "name": "Stairs", "type": "staircase"},
        {"id": "r", "name": "Room", "type": "room"},
        {"id": "w", "name": "Waypoint", "type": "waypoint"},
    ]
    monkeypatch.setattr(manager, "read_json_files", lambda: (nodes, []))

    entrances, classrooms = manager.get_options()

    assert entrances == [
        {"id": "e", "name": "Elevator"},
        {"id": "s", "name": "Stairs"},
    ]
    assert classrooms == [{"id": "r", "name": "Room"}]


def test_get_directions_returns_instructions_and_route_coordinates():
    manager.G = make_graph(
        ("start", node(floor=1, x=1, y=2)),
        ("middle", node(floor=1, x=3, y=4)),
        ("end", node(floor=1, x=5, y=6)),
        edges=[
            ("start", "middle", {"weight": 1, "instruction": "Walk ahead."}),
            ("middle", "end", {"weight": 1, "instruction": "Turn right."}),
        ],
    )

    result = manager.get_directions("start", "end")

    assert result == {
        "directions": ["Walk ahead.", "Turn right."],
        "coordinates": [
            {"x": 1, "y": 2, "floor": 1},
            {"x": 3, "y": 4, "floor": 1},
            {"x": 5, "y": 6, "floor": 1},
        ],
    }


def test_get_directions_handles_same_start_and_destination():
    manager.G = make_graph(("room", node(floor=5, x=12, y=-3)))

    assert manager.get_directions("room", "room") == {
        "directions": ["You are already at your destination."],
        "coordinates": [{"x": 12, "y": -3, "floor": 5}],
    }


@pytest.mark.parametrize(
    ("current_type", "next_type", "expected"),
    [
        ("staircase", "waypoint", "Take the stairs from floor 1 to floor 2."),
        ("waypoint", "staircase", "Take the stairs from floor 1 to floor 2."),
        ("elevator", "waypoint", "Move from floor 1 to floor 2."),
        ("waypoint", "elevator", "Move from floor 1 to floor 2."),
        ("waypoint", "waypoint", "Move from floor 1 to floor 2."),
    ],
)
def test_get_directions_describes_floor_changes(current_type, next_type, expected):
    manager.G = make_graph(
        ("start", node(floor=1, node_type=current_type)),
        ("end", node(floor=2, node_type=next_type)),
        edges=[("start", "end", {"weight": 1, "instruction": "Ignore me."})],
    )

    result = manager.get_directions("start", "end")

    assert result["directions"] == [expected]
    assert [coordinate["floor"] for coordinate in result["coordinates"]] == [1, 2]


def test_get_directions_preserves_generated_elevator_instruction_between_connectors():
    manager.G = make_graph(
        ("NPB_5_E1", node(floor=5, node_type="elevator")),
        ("NPB_4_E1", node(floor=4, node_type="elevator")),
        edges=[
            (
                "NPB_5_E1",
                "NPB_4_E1",
                {
                    "weight": 20,
                    "instruction": "Take elevator E1 to floor 4.",
                },
            )
        ],
    )

    result = manager.get_directions("NPB_5_E1", "NPB_4_E1")

    assert result["directions"] == ["Take elevator E1 to floor 4."]


def test_get_directions_returns_message_when_no_path_exists():
    manager.G = make_graph(("start", node()), ("end", node()))

    assert manager.get_directions("start", "end") == "No path found from start to end."


@pytest.mark.parametrize(
    ("start", "end"),
    [("missing", "end"), ("start", "missing")],
)
def test_get_directions_returns_message_for_missing_nodes(start, end):
    manager.G = make_graph(("start", node()), ("end", node()))

    assert manager.get_directions(start, end) == (
        f"No path found from {start} to {end}."
    )


def test_get_directions_uses_weighted_route_instructions():
    manager.G = make_graph(
        ("start", node(x=0, y=0)),
        ("direct", node(x=10, y=0)),
        ("detour", node(x=2, y=0)),
        ("end", node(x=4, y=0)),
        edges=[
            ("start", "direct", {"weight": 10, "instruction": "Take direct."}),
            ("direct", "end", {"weight": 10, "instruction": "Finish direct."}),
            ("start", "detour", {"weight": 2, "instruction": "Take detour."}),
            ("detour", "end", {"weight": 3, "instruction": "Finish detour."}),
        ],
    )

    result = manager.get_directions("start", "end")

    assert result["directions"] == ["Take detour.", "Finish detour."]
    assert [coordinate["x"] for coordinate in result["coordinates"]] == [0, 2, 4]


def test_get_directions_reuses_cached_graph(monkeypatch):
    manager.G = make_graph(
        ("start", node()),
        ("end", node()),
        edges=[("start", "end", {"weight": 1, "instruction": "Arrive."})],
    )
    reload_calls = []
    monkeypatch.setattr(manager, "reload_graph", lambda: reload_calls.append(True))

    assert manager.get_directions("start", "end")["directions"] == ["Arrive."]
    assert reload_calls == []


def test_get_directions_lazily_loads_graph(monkeypatch):
    graph = make_graph(
        ("start", node()),
        ("end", node()),
        edges=[("start", "end", {"weight": 1, "instruction": "Arrive."})],
    )

    def load_graph():
        manager.G = graph

    monkeypatch.setattr(manager, "reload_graph", load_graph)

    assert manager.get_directions("start", "end")["directions"] == ["Arrive."]


def test_main_draws_positioned_subgraph_and_saves_preview(monkeypatch):
    nodes = [
        {"id": "positioned", "coords": [10, 20]},
        {"id": "unpositioned", "coords": [None, 30]},
    ]
    graph = make_graph(
        ("positioned", node(x=10, y=20)),
        ("unpositioned", node(x=None, y=30)),
        edges=[("positioned", "unpositioned", {"weight": 1, "instruction": "Go."})],
    )
    drawn = []
    saved = []
    direction_calls = []
    monkeypatch.setattr(manager, "read_json_files", lambda: (nodes, []))
    monkeypatch.setattr(manager, "build_graph", lambda: graph)
    monkeypatch.setattr(
        manager.nx,
        "draw",
        lambda graph, pos, **kwargs: drawn.append((graph, pos, kwargs)),
    )
    monkeypatch.setattr(manager.plt, "savefig", lambda path: saved.append(path))
    monkeypatch.setattr(
        manager,
        "get_directions",
        lambda start, end: direction_calls.append((start, end)),
    )

    manager.main()

    assert manager.G is graph
    assert len(drawn) == 1
    assert set(drawn[0][0].nodes) == {"positioned"}
    assert drawn[0][1] == {"positioned": (10, 20)}
    assert saved == ["map_preview.png"]
    assert direction_calls == [("NPB_5_102", "NPB_5_E1")]


def test_logic_exports_public_graph_manager_api():
    assert logic.__all__ == ["get_directions", "get_floor_bounds", "get_options"]
    assert logic.get_directions is manager.get_directions
    assert logic.get_floor_bounds is manager.get_floor_bounds
    assert logic.get_options is manager.get_options
