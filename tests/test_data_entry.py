import json

import pytest

from app.logic import data_entry


def set_data_files(monkeypatch, tmp_path):
    nodes_file = tmp_path / "nested" / "nodes.json"
    edges_file = tmp_path / "nested" / "edges.json"
    monkeypatch.setattr(data_entry, "NODES_FILE", nodes_file)
    monkeypatch.setattr(data_entry, "EDGES_FILE", edges_file)
    return nodes_file, edges_file


def test_load_json_returns_empty_list_for_missing_file(tmp_path):
    assert data_entry.load_json(tmp_path / "missing.json") == []


def test_load_json_reads_data_and_reports_malformed_json(tmp_path, capsys):
    path = tmp_path / "data.json"
    path.write_text('{"valid": true}', encoding="utf-8")
    assert data_entry.load_json(path) == {"valid": True}

    path.write_text("not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        data_entry.load_json(path)
    assert "Failed to parse JSON file" in capsys.readouterr().out


def test_save_json_creates_parent_and_round_trips_data(tmp_path):
    path = tmp_path / "new" / "data.json"
    expected = [{"id": "room"}]

    data_entry.save_json(path, expected)

    assert json.loads(path.read_text(encoding="utf-8")) == expected


def test_add_node_rejects_duplicate_without_prompting_for_details(
    monkeypatch, tmp_path, capsys
):
    nodes_file, _ = set_data_files(monkeypatch, tmp_path)
    existing = [{"id": "room", "name": "Existing"}]
    data_entry.save_json(nodes_file, existing)
    input_values = iter(["room"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    data_entry.add_node()

    assert data_entry.load_json(nodes_file) == existing
    assert "already exists" in capsys.readouterr().out


def test_add_node_saves_normalized_values(monkeypatch, tmp_path):
    nodes_file, _ = set_data_files(monkeypatch, tmp_path)
    input_values = iter([" room ", "12.5", "-3", " Room 101 ", " room ", "4"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    data_entry.add_node()

    assert data_entry.load_json(nodes_file) == [
        {
            "id": "room",
            "name": "Room 101",
            "type": "room",
            "coords": [12.5, -3.0],
            "floor": 4,
        }
    ]


@pytest.mark.parametrize(
    ("invalid_input_index", "invalid_value"),
    [(1, "not-a-number"), (2, "not-a-number"), (5, "not-a-floor")],
)
def test_add_node_does_not_write_when_numeric_input_is_invalid(
    monkeypatch, tmp_path, invalid_input_index, invalid_value
):
    nodes_file, _ = set_data_files(monkeypatch, tmp_path)
    existing = [{"id": "existing", "name": "Existing"}]
    data_entry.save_json(nodes_file, existing)
    before = nodes_file.read_bytes()
    values = ["new", "1", "2", "New room", "room", "1"]
    values[invalid_input_index] = invalid_value
    input_values = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    with pytest.raises(ValueError):
        data_entry.add_node()

    assert nodes_file.read_bytes() == before
    assert data_entry.load_json(nodes_file) == existing


def test_add_edge_rejects_unknown_nodes(monkeypatch, tmp_path, capsys):
    nodes_file, edges_file = set_data_files(monkeypatch, tmp_path)
    data_entry.save_json(nodes_file, [{"id": "known"}])
    input_values = iter(["known", "missing", "2", "Go there"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    data_entry.add_edge()

    assert not edges_file.exists()
    assert "missing" in capsys.readouterr().out


def test_add_edge_saves_valid_connection(monkeypatch, tmp_path):
    nodes_file, edges_file = set_data_files(monkeypatch, tmp_path)
    data_entry.save_json(nodes_file, [{"id": "a"}, {"id": "b"}])
    input_values = iter([" a ", " b ", "2.5", " Turn right. "])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    data_entry.add_edge()

    assert data_entry.load_json(edges_file) == [
        {
            "source": "a",
            "target": "b",
            "weight": 2.5,
            "instruction": "Turn right.",
        }
    ]


def test_add_edge_reports_all_unknown_endpoints_without_writing(
    monkeypatch, tmp_path, capsys
):
    nodes_file, edges_file = set_data_files(monkeypatch, tmp_path)
    data_entry.save_json(nodes_file, [{"id": "known"}])
    existing_edges = [{"source": "known", "target": "known", "weight": 1}]
    data_entry.save_json(edges_file, existing_edges)
    before = edges_file.read_bytes()
    input_values = iter(["missing-start", "missing-end", "2", "Go there"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    data_entry.add_edge()

    assert edges_file.read_bytes() == before
    assert data_entry.load_json(edges_file) == existing_edges
    output = capsys.readouterr().out
    assert "missing-start" in output
    assert "missing-end" in output


def test_main_reports_invalid_choice_then_exits(monkeypatch, capsys):
    input_values = iter(["not-an-option", "3"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(input_values))

    data_entry.main()

    output = capsys.readouterr().out
    assert "Invalid option" in output
    assert "Exiting..." in output
