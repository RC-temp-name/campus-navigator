import runpy
from pathlib import Path
from unittest.mock import Mock

import pytest


def test_app_factory_registers_blueprint_without_loading_graph(monkeypatch):
    """Creating the Flask app must not read or build the graph."""
    from app import create_app
    from app.logic import graph_manager

    read_json_files = Mock(side_effect=AssertionError("graph data loaded too early"))
    build_graph = Mock(side_effect=AssertionError("graph built too early"))
    monkeypatch.setattr(graph_manager, "read_json_files", read_json_files)
    monkeypatch.setattr(graph_manager, "build_graph", build_graph)

    app = create_app()

    assert app.blueprints["main"].name == "main"
    rules = {rule.rule: rule for rule in app.url_map.iter_rules()}
    assert {"GET", "HEAD", "OPTIONS"} <= rules["/"].methods
    assert {"POST", "OPTIONS"} <= rules["/directions"].methods
    assert {"GET", "HEAD", "OPTIONS"} <= rules["/api/test"].methods
    assert rules["/"].endpoint == "main.index"
    assert rules["/directions"].endpoint == "main.directions"
    assert rules["/api/test"].endpoint == "main.test"
    read_json_files.assert_not_called()
    build_graph.assert_not_called()


@pytest.mark.parametrize(
    ("debug_value", "expected_debug"),
    [
        (None, False),
        ("0", False),
        ("false", False),
        ("1", True),
        ("true", True),
        ("True", True),
    ],
)
def test_run_entry_point_passes_debug_environment_to_flask(
    monkeypatch, debug_value, expected_debug
):
    if debug_value is None:
        monkeypatch.delenv("FLASK_DEBUG", raising=False)
    else:
        monkeypatch.setenv("FLASK_DEBUG", debug_value)

    run_server = Mock()
    monkeypatch.setattr("flask.Flask.run", run_server)

    namespace = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "run.py"), run_name="__main__"
    )

    assert namespace["app"].name == "app"
    run_server.assert_called_once_with(debug=expected_debug)
