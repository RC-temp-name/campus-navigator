import csv
import json
from pathlib import Path

from tools import generate_vertical_edges, validate_data

REPO_ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = REPO_ROOT / "data" / "nodes.json"
EDGES_PATH = REPO_ROOT / "data" / "edges.json"
FLOORS_PATH = REPO_ROOT / "data" / "floors.json"
ROOMS_CSV_PATH = REPO_ROOT / "tools" / "npb_rooms.csv"

NODE_FIELDS = {"id", "name", "type", "building", "floor", "coords"}
EDGE_FIELDS = {"source", "target", "weight", "instruction"}
FLOOR_FIELDS = {
    "width_feet",
    "height_feet",
    "px_per_foot",
    "origin_px",
}
ROOMS_CSV_FIELDS = ["id", "name", "building", "floor", "type"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def test_canonical_data_has_consistent_schemas_and_is_not_mutated(capsys):
    paths = [NODES_PATH, EDGES_PATH, FLOORS_PATH, ROOMS_CSV_PATH]
    before = {path: path.read_bytes() for path in paths}

    nodes = read_json(NODES_PATH)
    edges = read_json(EDGES_PATH)
    floors = read_json(FLOORS_PATH)

    assert isinstance(nodes, list) and nodes
    assert isinstance(edges, list) and edges
    assert isinstance(floors, dict) and floors

    node_ids = set()
    for node in nodes:
        assert set(node) == NODE_FIELDS
        assert isinstance(node["id"], str) and node["id"]
        assert node["id"] not in node_ids
        node_ids.add(node["id"])
        assert isinstance(node["name"], str) and node["name"].strip()
        assert isinstance(node["type"], str) and node["type"].strip()
        assert isinstance(node["building"], str) and node["building"].strip()
        assert isinstance(node["floor"], int) and not isinstance(node["floor"], bool)
        assert node["id"].startswith(f"{node['building']}_{node['floor']}_")
        assert (
            isinstance(node["coords"], list)
            and len(node["coords"]) == 2
            and all(is_number(value) for value in node["coords"])
        )

    edge_pairs = set()
    for edge in edges:
        assert set(edge) == EDGE_FIELDS
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids
        assert is_number(edge["weight"])
        assert isinstance(edge["instruction"], str)
        assert edge["instruction"].strip()
        edge_pairs.add((edge["source"], edge["target"]))

    assert len(edge_pairs) == len(edges)
    assert all((target, source) in edge_pairs for source, target in edge_pairs)

    assert set(floors) == {"NPB"}
    assert set(floors["NPB"]) == {"1", "2", "3", "4", "5"}
    for floor in floors["NPB"].values():
        assert set(floor) == FLOOR_FIELDS
        assert is_number(floor["width_feet"]) and floor["width_feet"] > 0
        assert is_number(floor["height_feet"]) and floor["height_feet"] > 0
        if floor["px_per_foot"] is None:
            assert floor["origin_px"] is None
        else:
            assert is_number(floor["px_per_foot"]) and floor["px_per_foot"] > 0
            assert (
                isinstance(floor["origin_px"], list)
                and len(floor["origin_px"]) == 2
                and all(is_number(value) for value in floor["origin_px"])
            )

    with ROOMS_CSV_PATH.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == ROOMS_CSV_FIELDS
        rows = list(reader)

    assert rows
    room_ids = set()
    for row in rows:
        assert set(row) == set(ROOMS_CSV_FIELDS)
        assert all(isinstance(value, str) and value.strip() for value in row.values())
        assert row["id"] not in room_ids
        room_ids.add(row["id"])
        assert row["building"] == "NPB"
        floor = int(row["floor"])
        assert str(floor) in floors["NPB"]
        assert row["id"].startswith(f"{row['building']}_{floor}_")

    # The validator reports the canonical JSON without writing any of it.
    validate_data.main()
    assert "Data OK — 277 nodes, 580 edges (580 connections)" in capsys.readouterr().out

    assert {path: path.read_bytes() for path in paths} == before


def test_canonical_vertical_connections_are_present_in_edges():
    nodes = read_json(NODES_PATH)
    edges = read_json(EDGES_PATH)
    connectors = generate_vertical_edges.discover_connectors(nodes)
    generated = generate_vertical_edges.generate_edges(connectors)
    persisted = {
        (edge["source"], edge["target"], edge["weight"], edge["instruction"])
        for edge in edges
    }

    assert set(connectors) == {
        ("NPB", "E1"),
        ("NPB", "E3"),
        ("NPB", "S1"),
        ("NPB", "S2"),
        ("NPB", "stairs_main"),
    }
    assert all(info["floors"] == [3, 4, 5] for info in connectors.values())
    assert len(generated) == 24
    assert all(
        (edge["source"], edge["target"], edge["weight"], edge["instruction"])
        in persisted
        for edge in generated
    )

    # This independent count makes the elevator/stair rules explicit for the
    # checked-in three-floor dataset: 3 elevators x 6 directed pairs and 3
    # staircases x 4 directed adjacent pairs.
    assert len([edge for edge in generated if "_E" in edge["source"]]) == 12
    assert (
        len(
            [
                edge
                for edge in generated
                if "_S" in edge["source"] or "stairs_main" in edge["source"]
            ]
        )
        == 12
    )
