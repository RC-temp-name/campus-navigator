import json
import sys

import pytest

from tools import csv_import


def configure_nodes_path(monkeypatch, tmp_path):
    path = tmp_path / "data" / "nodes.json"
    monkeypatch.setattr(csv_import, "NODES_PATH", path)
    return path


def test_load_nodes_returns_empty_list_when_file_is_missing(monkeypatch, tmp_path):
    configure_nodes_path(monkeypatch, tmp_path)

    assert csv_import.load_nodes() == []


def test_main_imports_new_nodes_and_skips_duplicates(monkeypatch, tmp_path, capsys):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    nodes_path.write_text(json.dumps([{"id": "existing", "name": "Existing"}]))
    csv_path = tmp_path / "rooms.csv"
    csv_path.write_text(
        "id,name,building,floor,type\n"
        "existing,Old Name,BLDG,1,room\n"
        "# comment,Ignored,BLDG,1,room\n"
        ",Blank,BLDG,1,room\n"
        "new,New Room,BLDG,3,room\n"
        "new,Duplicate,BLDG,4,room\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["csv_import.py", str(csv_path)])

    csv_import.main()

    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    assert nodes == [
        {"id": "existing", "name": "Existing"},
        {
            "id": "new",
            "name": "New Room",
            "type": "room",
            "building": "BLDG",
            "coords": [0, 0],
            "floor": 3,
        },
    ]
    output = capsys.readouterr().out
    assert "SKIP (already exists): existing" in output
    assert "Done: 1 node(s) added, 2 skipped." in output


def test_main_uses_default_csv_path_when_no_argument(monkeypatch, tmp_path):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    csv_path = tmp_path / "default.csv"
    csv_path.write_text("id,name,building,floor,type\nroom,Room,BLDG,1,room\n")
    monkeypatch.setattr(csv_import, "DEFAULT_CSV", csv_path)
    monkeypatch.setattr(sys, "argv", ["csv_import.py"])

    csv_import.main()

    assert json.loads(nodes_path.read_text(encoding="utf-8"))[0]["id"] == "room"


def test_main_ignores_blank_lines_and_comment_or_blank_ids(monkeypatch, tmp_path):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    csv_path = tmp_path / "rooms.csv"
    csv_path.write_text(
        "id,name,building,floor,type\n"
        "\n"
        "  # comment,Ignored,BLDG,1,room\n"
        "   ,No ID,BLDG,1,room\n"
        "room,Room,BLDG,1,room\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["csv_import.py", str(csv_path)])

    csv_import.main()

    assert json.loads(nodes_path.read_text(encoding="utf-8")) == [
        {
            "id": "room",
            "name": "Room",
            "type": "room",
            "building": "BLDG",
            "coords": [0, 0],
            "floor": 1,
        }
    ]


def test_main_strips_node_fields_from_explicit_csv_path(monkeypatch, tmp_path):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    csv_path = tmp_path / "rooms.csv"
    csv_path.write_text(
        "id,name,building,floor,type\n room , Room 101 , BLDG , 2 , classroom \n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["csv_import.py", str(csv_path)])

    csv_import.main()

    assert json.loads(nodes_path.read_text(encoding="utf-8")) == [
        {
            "id": "room",
            "name": "Room 101",
            "type": "classroom",
            "building": "BLDG",
            "coords": [0, 0],
            "floor": 2,
        }
    ]


def test_main_uses_defaults_for_missing_csv_columns(monkeypatch, tmp_path):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    csv_path = tmp_path / "rooms.csv"
    csv_path.write_text("id\n  room_101  \n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["csv_import.py", str(csv_path)])

    csv_import.main()

    assert json.loads(nodes_path.read_text(encoding="utf-8")) == [
        {
            "id": "room_101",
            "name": "room_101",
            "type": "room",
            "building": "",
            "coords": [0, 0],
            "floor": 1,
        }
    ]


def test_load_nodes_raises_for_malformed_json_without_writing(monkeypatch, tmp_path):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    malformed = '{"nodes":'
    nodes_path.write_text(malformed, encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        csv_import.load_nodes()

    assert nodes_path.read_text(encoding="utf-8") == malformed


def test_main_does_not_write_partial_import_when_floor_conversion_fails(
    monkeypatch, tmp_path
):
    nodes_path = configure_nodes_path(monkeypatch, tmp_path)
    nodes_path.parent.mkdir()
    existing = [{"id": "existing", "name": "Existing"}]
    nodes_path.write_text(json.dumps(existing), encoding="utf-8")
    before = nodes_path.read_bytes()
    csv_path = tmp_path / "rooms.csv"
    csv_path.write_text(
        "id,name,building,floor,type\n"
        "new,New Room,BLDG,2,room\n"
        "broken,Broken Room,BLDG,not-a-floor,room\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["csv_import.py", str(csv_path)])

    with pytest.raises(ValueError):
        csv_import.main()

    assert nodes_path.read_bytes() == before
    assert json.loads(nodes_path.read_text(encoding="utf-8")) == existing


def test_main_exits_when_csv_file_is_missing(monkeypatch, tmp_path, capsys):
    configure_nodes_path(monkeypatch, tmp_path)
    missing = tmp_path / "missing.csv"
    monkeypatch.setattr(sys, "argv", ["csv_import.py", str(missing)])

    with pytest.raises(SystemExit) as exc_info:
        csv_import.main()

    assert exc_info.value.code == 1
    assert f"CSV file not found: {missing}" in capsys.readouterr().out
