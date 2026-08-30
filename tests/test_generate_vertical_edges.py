import json

import pytest

from tools import generate_vertical_edges as generator


def test_load_json_returns_empty_list_when_missing(tmp_path):
    assert generator.load_json(tmp_path / "missing.json") == []


def test_load_json_propagates_malformed_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        generator.load_json(path)


def test_save_json_creates_expected_json(tmp_path):
    path = tmp_path / "nested" / "edges.json"
    data = [{"source": "a", "target": "b"}]

    path.parent.mkdir()
    generator.save_json(path, data)

    assert json.loads(path.read_text(encoding="utf-8")) == data


def test_save_json_propagates_persistence_failure():
    class BrokenPath:
        def open(self, *args, **kwargs):
            raise OSError("disk full")

    with pytest.raises(OSError, match="disk full"):
        generator.save_json(BrokenPath(), [])


def test_discover_connectors_keys_by_building_and_deduplicates_floors():
    nodes = [
        {"id": "BLDG_5_E1", "floor": 5, "name": "E1", "building": "BLDG"},
        {"id": "BLDG_3_E1", "floor": 3, "name": "E1", "building": "BLDG"},
        {
            "id": "BLDG_4_stairs_main",
            "floor": 4,
            "name": "Main Stairs",
            "building": "BLDG",
        },
        {
            "id": "BLDG_2_stairs_main",
            "floor": 2,
            "name": "Main Stairs",
            "building": "BLDG",
        },
        {
            "id": "BLDG_4_stairs_main",
            "floor": 4,
            "name": "Main Stairs",
            "building": "BLDG",
        },
        {"id": "SCI_1_S1", "floor": 1, "name": "S1", "building": "SCI"},
        {"id": "BLDG_2_E2", "floor": 2, "name": "Unknown", "building": "BLDG"},
        {"id": "short", "floor": 1, "name": "Short", "building": "BLDG"},
    ]

    connectors = generator.discover_connectors(nodes)

    assert connectors == {
        ("BLDG", "E1"): {
            "type": "elevator",
            "floors": [3, 5],
            "name": "E1",
            "building": "BLDG",
        },
        ("BLDG", "stairs_main"): {
            "type": "staircase",
            "floors": [2, 4],
            "name": "Main Stairs",
            "building": "BLDG",
        },
        ("SCI", "S1"): {
            "type": "staircase",
            "floors": [1],
            "name": "S1",
            "building": "SCI",
        },
    }


def test_discover_connectors_keeps_same_suffixes_in_separate_buildings():
    nodes = [
        {"id": "BLDG_1_E1", "floor": 1, "name": "BLDG E1", "building": "BLDG"},
        {"id": "BLDG_2_E1", "floor": 2, "name": "BLDG E1", "building": "BLDG"},
        {"id": "SCI_1_E1", "floor": 1, "name": "SCI E1", "building": "SCI"},
        {"id": "SCI_2_E1", "floor": 2, "name": "SCI E1", "building": "SCI"},
    ]

    connectors = generator.discover_connectors(nodes)

    assert set(connectors) == {("BLDG", "E1"), ("SCI", "E1")}
    assert {
        (edge["source"], edge["target"])
        for edge in generator.generate_edges(connectors)
    } == {
        ("BLDG_1_E1", "BLDG_2_E1"),
        ("BLDG_2_E1", "BLDG_1_E1"),
        ("SCI_1_E1", "SCI_2_E1"),
        ("SCI_2_E1", "SCI_1_E1"),
    }


def test_discover_connectors_uses_building_from_id_when_field_is_missing():
    nodes = [{"id": "NPB_2_E3", "floor": 2, "name": "E3"}]

    assert generator.discover_connectors(nodes)[("NPB", "E3")]["building"] == "NPB"


def test_discover_connectors_rejects_building_id_mismatch():
    nodes = [{"id": "NPB_2_E3", "floor": 2, "name": "E3", "building": "SCI"}]

    with pytest.raises(ValueError, match="has building 'SCI'.*ID uses 'NPB'"):
        generator.discover_connectors(nodes)


def test_generate_edges_deduplicates_elevator_floors_without_self_edges():
    connectors = {
        ("NPB", "E1"): {
            "type": "elevator",
            "floors": [1, 2, 2],
            "name": "E1",
            "building": "NPB",
        }
    }

    edges = generator.generate_edges(connectors)

    assert {(edge["source"], edge["target"]) for edge in edges} == {
        ("NPB_1_E1", "NPB_2_E1"),
        ("NPB_2_E1", "NPB_1_E1"),
    }


def test_generate_edges_uses_all_elevator_pairs_but_only_adjacent_stairs():
    connectors = {
        "E1": {
            "type": "elevator",
            "floors": [1, 3, 5],
            "name": "E1",
            "building": "BLDG",
        },
        "S1": {
            "type": "staircase",
            "floors": [1, 2, 4],
            "name": "S1",
            "building": "BLDG",
        },
    }

    edges = generator.generate_edges(connectors)

    assert len(edges) == 8
    assert {
        (edge["source"], edge["target"]) for edge in edges if "E1" in edge["source"]
    } == {
        ("BLDG_1_E1", "BLDG_3_E1"),
        ("BLDG_3_E1", "BLDG_1_E1"),
        ("BLDG_1_E1", "BLDG_5_E1"),
        ("BLDG_5_E1", "BLDG_1_E1"),
        ("BLDG_3_E1", "BLDG_5_E1"),
        ("BLDG_5_E1", "BLDG_3_E1"),
    }
    stairs = [edge for edge in edges if "S1" in edge["source"]]
    assert {(edge["source"], edge["target"]) for edge in stairs} == {
        ("BLDG_1_S1", "BLDG_2_S1"),
        ("BLDG_2_S1", "BLDG_1_S1"),
    }

    elevator_up = next(
        edge
        for edge in edges
        if edge["source"] == "BLDG_1_E1" and edge["target"] == "BLDG_5_E1"
    )
    assert elevator_up == {
        "source": "BLDG_1_E1",
        "target": "BLDG_5_E1",
        "weight": 80,
        "instruction": "Take elevator E1 to floor 5.",
    }
    assert next(
        edge
        for edge in edges
        if edge["source"] == "BLDG_5_E1" and edge["target"] == "BLDG_1_E1"
    ) == {
        "source": "BLDG_5_E1",
        "target": "BLDG_1_E1",
        "weight": 80,
        "instruction": "Take elevator E1 to floor 1.",
    }
    assert next(edge for edge in edges if edge["source"] == "BLDG_1_S1") == {
        "source": "BLDG_1_S1",
        "target": "BLDG_2_S1",
        "weight": 20,
        "instruction": "Take the stairs to floor 2.",
    }
    assert next(edge for edge in edges if edge["source"] == "BLDG_2_S1") == {
        "source": "BLDG_2_S1",
        "target": "BLDG_1_S1",
        "weight": 20,
        "instruction": "Take the stairs to floor 1.",
    }


def test_generate_edges_ignores_stair_gaps_and_duplicate_floors():
    connectors = {
        "stairs_main": {
            "type": "staircase",
            "floors": [1, 2, 2, 4],
            "name": "Main Stairs",
            "building": "NPB",
        }
    }

    edges = generator.generate_edges(connectors)

    assert {(edge["source"], edge["target"]) for edge in edges} == {
        ("NPB_1_stairs_main", "NPB_2_stairs_main"),
        ("NPB_2_stairs_main", "NPB_1_stairs_main"),
    }
    assert all(edge["source"] != edge["target"] for edge in edges)


def test_generate_edges_returns_no_edges_without_connectors():
    assert generator.generate_edges({}) == []


def test_main_appends_only_new_vertical_edges(monkeypatch, tmp_path, capsys):
    nodes_path = tmp_path / "nodes.json"
    edges_path = tmp_path / "edges.json"
    nodes = [
        {"id": "BLDG_1_E1", "floor": 1, "name": "E1", "building": "BLDG"},
        {"id": "BLDG_2_E1", "floor": 2, "name": "E1", "building": "BLDG"},
    ]
    existing = [
        {
            "source": "BLDG_1_E1",
            "target": "BLDG_2_E1",
            "weight": 20,
            "instruction": "Existing",
        }
    ]
    nodes_path.write_text(json.dumps(nodes), encoding="utf-8")
    edges_path.write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(generator, "NODES_PATH", nodes_path)
    monkeypatch.setattr(generator, "EDGES_PATH", edges_path)

    generator.main()

    assert json.loads(edges_path.read_text(encoding="utf-8")) == existing + [
        {
            "source": "BLDG_2_E1",
            "target": "BLDG_1_E1",
            "weight": 20,
            "instruction": "Take elevator E1 to floor 1.",
        }
    ]
    assert "1 edge(s) added, 1 skipped" in capsys.readouterr().out


def test_main_is_idempotent_when_run_twice(monkeypatch, tmp_path, capsys):
    nodes_path = tmp_path / "nodes.json"
    edges_path = tmp_path / "edges.json"
    nodes_path.write_text(
        json.dumps(
            [
                {
                    "id": "BLDG_1_E1",
                    "floor": 1,
                    "name": "E1",
                    "building": "BLDG",
                },
                {
                    "id": "BLDG_2_E1",
                    "floor": 2,
                    "name": "E1",
                    "building": "BLDG",
                },
            ]
        ),
        encoding="utf-8",
    )
    edges_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(generator, "NODES_PATH", nodes_path)
    monkeypatch.setattr(generator, "EDGES_PATH", edges_path)

    generator.main()
    first_run = json.loads(edges_path.read_text(encoding="utf-8"))
    generator.main()
    second_run = json.loads(edges_path.read_text(encoding="utf-8"))

    assert len(first_run) == len(second_run) == 2
    assert second_run == first_run
    output = capsys.readouterr().out
    assert "Done: 2 edge(s) added, 0 skipped." in output
    assert "Done: 0 edge(s) added, 2 skipped." in output


def test_main_does_not_write_when_no_connectors_are_found(
    monkeypatch, tmp_path, capsys
):
    nodes_path = tmp_path / "nodes.json"
    edges_path = tmp_path / "edges.json"
    nodes_path.write_text(
        json.dumps([{"id": "BLDG_2_E2", "floor": 2, "name": "Unknown"}]),
        encoding="utf-8",
    )
    original_edges = [{"source": "a", "target": "b"}]
    edges_path.write_text(json.dumps(original_edges), encoding="utf-8")
    monkeypatch.setattr(generator, "NODES_PATH", nodes_path)
    monkeypatch.setattr(generator, "EDGES_PATH", edges_path)
    monkeypatch.setattr(
        generator,
        "save_json",
        lambda *_args: pytest.fail("save_json should not run without connectors"),
    )

    generator.main()

    assert json.loads(edges_path.read_text(encoding="utf-8")) == original_edges
    assert "No connectors found in nodes.json" in capsys.readouterr().out


def test_main_treats_missing_edges_file_as_empty(monkeypatch, tmp_path):
    nodes_path = tmp_path / "nodes.json"
    edges_path = tmp_path / "missing-edges.json"
    nodes_path.write_text(
        json.dumps(
            [
                {
                    "id": "BLDG_1_E1",
                    "floor": 1,
                    "name": "E1",
                    "building": "BLDG",
                },
                {
                    "id": "BLDG_2_E1",
                    "floor": 2,
                    "name": "E1",
                    "building": "BLDG",
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(generator, "NODES_PATH", nodes_path)
    monkeypatch.setattr(generator, "EDGES_PATH", edges_path)

    generator.main()

    assert len(json.loads(edges_path.read_text(encoding="utf-8"))) == 2


def test_main_handles_missing_input_files_without_creating_edges_file(
    monkeypatch, tmp_path, capsys
):
    nodes_path = tmp_path / "missing-nodes.json"
    edges_path = tmp_path / "missing-edges.json"
    monkeypatch.setattr(generator, "NODES_PATH", nodes_path)
    monkeypatch.setattr(generator, "EDGES_PATH", edges_path)

    generator.main()

    assert not edges_path.exists()
    assert "No connectors found in nodes.json" in capsys.readouterr().out


def test_main_propagates_edges_persistence_failure(monkeypatch, tmp_path):
    nodes_path = tmp_path / "nodes.json"
    edges_path = tmp_path / "edges.json"
    nodes_path.write_text(
        json.dumps(
            [
                {
                    "id": "BLDG_1_E1",
                    "floor": 1,
                    "name": "E1",
                    "building": "BLDG",
                },
                {
                    "id": "BLDG_2_E1",
                    "floor": 2,
                    "name": "E1",
                    "building": "BLDG",
                },
            ]
        ),
        encoding="utf-8",
    )
    edges_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(generator, "NODES_PATH", nodes_path)
    monkeypatch.setattr(generator, "EDGES_PATH", edges_path)

    def fail_to_save(*_args):
        raise OSError("cannot write edges")

    monkeypatch.setattr(generator, "save_json", fail_to_save)

    with pytest.raises(OSError, match="cannot write edges"):
        generator.main()
