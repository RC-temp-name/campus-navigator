import json

import pytest

from tools import validate_data


def write_data(monkeypatch, tmp_path, nodes, edges):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "nodes.json").write_text(json.dumps(nodes), encoding="utf-8")
    (data_dir / "edges.json").write_text(json.dumps(edges), encoding="utf-8")
    monkeypatch.setattr(validate_data, "DATA_DIR", data_dir)
    return data_dir


def valid_nodes():
    return [
        {
            "id": "BLDG_1_a",
            "name": "A",
            "type": "room",
            "building": "BLDG",
            "floor": 1,
            "coords": [1, 2],
        },
        {
            "id": "BLDG_1_b",
            "name": "B",
            "type": "waypoint",
            "building": "BLDG",
            "floor": 1,
            "coords": [3.5, 4],
        },
    ]


def valid_edges():
    return [
        {
            "source": "BLDG_1_a",
            "target": "BLDG_1_b",
            "weight": 2,
            "instruction": "Go forward.",
        },
        {
            "source": "BLDG_1_b",
            "target": "BLDG_1_a",
            "weight": 2,
            "instruction": "Turn around.",
        },
    ]


def test_main_accepts_valid_data_and_numeric_float_weights(
    monkeypatch, tmp_path, capsys
):
    edges = valid_edges()
    edges[0]["weight"] = 2.5
    write_data(monkeypatch, tmp_path, valid_nodes(), edges)

    validate_data.main()

    assert "Data OK — 2 nodes, 2 edges (2 connections)" in capsys.readouterr().out


def test_main_reports_non_blocking_prefix_warning(monkeypatch, tmp_path, capsys):
    nodes = valid_nodes()
    nodes[0]["id"] = "wrong-prefix"
    edges = [
        {
            "source": "wrong-prefix",
            "target": "BLDG_1_b",
            "weight": 2,
            "instruction": "Go forward.",
        },
        {
            "source": "BLDG_1_b",
            "target": "wrong-prefix",
            "weight": 2,
            "instruction": "Turn around.",
        },
    ]
    write_data(monkeypatch, tmp_path, nodes, edges)

    validate_data.main()

    output = capsys.readouterr().out
    assert "id doesn't start with building prefix 'BLDG_'" in output
    assert "Data OK — 2 nodes, 2 edges (2 connections)" in output
    assert "1 warning(s) above" in output


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "", "name must be non-empty text"),
        ("type", 1, "type must be non-empty text"),
        ("building", True, "building must be non-empty text"),
        ("floor", True, "floor must be an integer"),
    ],
)
def test_main_rejects_invalid_node_field_types(
    monkeypatch, tmp_path, field, value, message, capsys
):
    nodes = valid_nodes()
    nodes[0][field] = value
    write_data(monkeypatch, tmp_path, nodes, valid_edges())

    with pytest.raises(SystemExit) as exc_info:
        validate_data.main()

    assert exc_info.value.code == 1
    assert message in capsys.readouterr().out


def test_main_reports_reverse_edge_warning_without_exiting(
    monkeypatch, tmp_path, capsys
):
    write_data(monkeypatch, tmp_path, valid_nodes(), valid_edges()[:1])

    validate_data.main()

    output = capsys.readouterr().out
    assert "no reverse edge exists" in output
    assert "Data OK — 2 nodes, 1 edges (1 connections)" in output
    assert "1 warning(s) above" in output


def test_main_exits_and_reports_schema_and_reference_errors(
    monkeypatch, tmp_path, capsys
):
    nodes = valid_nodes() + [
        {
            "id": "BLDG_1_a",
            "name": "Duplicate",
            "type": "room",
            "building": "BLDG",
            "floor": 1,
            "coords": [0, 0],
        },
        {"id": "incomplete"},
    ]
    edges = [
        {
            "source": "BLDG_1_a",
            "target": "missing",
            "weight": "heavy",
            "instruction": "  ",
        },
        {"source": "BLDG_1_a"},
    ]
    write_data(monkeypatch, tmp_path, nodes, edges)

    with pytest.raises(SystemExit) as exc_info:
        validate_data.main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "duplicate node id 'BLDG_1_a'" in output
    assert "missing field(s)" in output
    assert "'missing' is not a known node id" in output
    assert "weight must be a number" in output
    assert "instruction must be non-empty text" in output
    assert "problem(s) found in data/" in output


@pytest.mark.parametrize(
    "coords",
    [[1], [1, 2, 3], "1,2", [1, "2"], [True, 2], None],
)
def test_main_rejects_invalid_coordinate_shapes(monkeypatch, tmp_path, coords, capsys):
    nodes = valid_nodes()
    nodes[0]["coords"] = coords
    write_data(monkeypatch, tmp_path, nodes, valid_edges())

    with pytest.raises(SystemExit) as exc_info:
        validate_data.main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "coords must be [x, y] numbers" in output
    assert "node 'BLDG_1_a'" in output


@pytest.mark.parametrize("instruction", ["", "  \n", None, 123])
def test_main_rejects_empty_or_non_text_instructions(
    monkeypatch, tmp_path, instruction, capsys
):
    edges = valid_edges()
    edges[0]["instruction"] = instruction
    write_data(monkeypatch, tmp_path, valid_nodes(), edges)

    with pytest.raises(SystemExit) as exc_info:
        validate_data.main()

    assert exc_info.value.code == 1
    assert "instruction must be non-empty text" in capsys.readouterr().out


@pytest.mark.parametrize("weight", ["2", None, [], {"cost": 2}, True, False])
def test_main_rejects_non_numeric_weights(monkeypatch, tmp_path, weight, capsys):
    edges = valid_edges()
    edges[0]["weight"] = weight
    write_data(monkeypatch, tmp_path, valid_nodes(), edges)

    with pytest.raises(SystemExit) as exc_info:
        validate_data.main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "weight must be a number" in output
    assert repr(weight) in output


@pytest.mark.parametrize(
    ("nodes", "edges", "message"),
    [
        (
            {"not": "a list"},
            valid_edges(),
            "nodes.json: top-level value must be a list",
        ),
        (
            valid_nodes(),
            {"not": "a list"},
            "edges.json: top-level value must be a list",
        ),
        (["not an object"], valid_edges(), "nodes.json[0]: entry must be an object"),
        (valid_nodes(), ["not an object"], "edges.json[0]: entry must be an object"),
    ],
)
def test_main_rejects_wrong_json_shapes_and_entries(
    monkeypatch, tmp_path, nodes, edges, message, capsys
):
    write_data(monkeypatch, tmp_path, nodes, edges)

    with pytest.raises(SystemExit) as exc_info:
        validate_data.main()

    assert exc_info.value.code == 1
    assert message in capsys.readouterr().out


@pytest.mark.parametrize("missing_name", ["nodes.json", "edges.json"])
def test_load_exits_for_missing_data_file(monkeypatch, tmp_path, missing_name, capsys):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(validate_data, "DATA_DIR", data_dir)

    with pytest.raises(SystemExit) as exc_info:
        validate_data.load(missing_name)

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "Missing file" in output
    assert missing_name in output


@pytest.mark.parametrize("filename", ["nodes.json", "edges.json"])
def test_load_exits_for_malformed_json(monkeypatch, tmp_path, filename, capsys):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / filename).write_text("{", encoding="utf-8")
    monkeypatch.setattr(validate_data, "DATA_DIR", data_dir)

    with pytest.raises(SystemExit) as exc_info:
        validate_data.load(filename)

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert f"{filename} is not valid JSON" in output
    assert "line 1" in output
