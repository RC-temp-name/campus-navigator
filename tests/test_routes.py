import json
import re
from unittest.mock import Mock

import pytest

from app import logic, routes
from app.logic import graph_manager

OPTIONS = (
    [{"id": "NPB_5_E1", "name": "5.E1 elevator"}],
    [{"id": "NPB_5_154", "name": "5.154"}],
)


@pytest.fixture(autouse=True)
def stub_options(monkeypatch):
    monkeypatch.setattr(routes, "get_options", lambda: OPTIONS)


def embedded_json(body, variable):
    """Read a JSON value exposed by the page's JavaScript contract."""
    match = re.search(
        rf"(?:window\.)?{re.escape(variable)}\s*=\s*(?P<value>.*?);",
        body,
        flags=re.DOTALL,
    )
    assert match, f"{variable} was not embedded in the response"
    return json.loads(match.group("value"))


def test_index_renders_form_options_and_map_placeholder(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "<h1>Choose Your Options</h1>" in body
    assert '<form method="post" action="/directions">' in body
    assert '<button type="submit">Get Directions</button>' in body
    assert '<select id="entrance" name="entrance">' in body
    assert 'value="NPB_5_E1">5.E1 elevator' in body
    assert '<select id="classroom" name="classroom">' in body
    assert 'value="NPB_5_154">5.154' in body
    assert "Map will appear here after you select directions" in body
    assert "/static/css/styles.css" in body
    assert "window.routeCoordinates" not in body


@pytest.mark.parametrize(
    "form_data",
    [
        {},
        {"entrance": "NPB_5_E1"},
        {"classroom": "NPB_5_154"},
        {"entrance": "", "classroom": "NPB_5_154"},
        {"entrance": "NPB_5_E1", "classroom": ""},
    ],
)
def test_directions_rejects_missing_form_values(client, monkeypatch, form_data):
    get_directions = Mock()
    monkeypatch.setattr(routes, "get_directions", get_directions)

    response = client.post("/directions", data=form_data)

    assert response.status_code == 200
    assert "Missing entrance or classroom parameter" in response.get_data(as_text=True)
    get_directions.assert_not_called()


def test_directions_only_accepts_post(client):
    response = client.get("/directions")

    assert response.status_code == 405


def test_live_index_and_multi_floor_post_use_canonical_data(client, monkeypatch):
    monkeypatch.setattr(routes, "get_options", logic.get_options)
    graph_manager.G = None

    index_response = client.get("/")
    assert index_response.status_code == 200
    index_body = index_response.get_data(as_text=True)
    assert 'value="NPB_5_E1">5.E1' in index_body
    assert 'value="NPB_4_440">4.440' in index_body

    response = client.post(
        "/directions",
        data={"entrance": "NPB_5_E1", "classroom": "NPB_4_440"},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Take elevator E1 to floor 4." in body
    assert "Map preview is unavailable for routes spanning multiple floors." in body
    assert "window.routeCoordinates" not in body


def test_directions_embeds_route_and_uses_entrance_building_and_first_floor(
    client, monkeypatch
):
    route = {
        "directions": ["Leave the elevator.", "Turn left at the hallway."],
        "coordinates": [
            {"x": 1, "y": 2, "floor": 4},
            {"x": 3.5, "y": -6, "floor": 4},
        ],
    }
    get_directions = Mock(return_value=route)
    get_floor_bounds = Mock(return_value={"width": 300, "height": 60})
    monkeypatch.setattr(routes, "get_directions", get_directions)
    monkeypatch.setattr(routes, "get_floor_bounds", get_floor_bounds)

    response = client.post(
        "/directions",
        data={"entrance": "NPB_5_E1", "classroom": "NPB_5_154"},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert embedded_json(body, "directionSteps") == route["directions"]
    assert embedded_json(body, "routeCoordinates") == route["coordinates"]
    assert embedded_json(body, "floorBounds") == {"width": 300, "height": 60}
    assert 'id="directions-panel"' in body
    assert "/static/js/directions.js" in body
    assert "/static/js/map.js" in body
    get_directions.assert_called_once_with("NPB_5_E1", "NPB_5_154")
    get_floor_bounds.assert_called_once_with("NPB", 4)


def test_directions_displays_no_route_error(client, monkeypatch):
    get_directions = Mock(return_value="No path found from start to end.")
    get_floor_bounds = Mock()
    monkeypatch.setattr(routes, "get_directions", get_directions)
    monkeypatch.setattr(routes, "get_floor_bounds", get_floor_bounds)

    response = client.post(
        "/directions",
        data={"entrance": "NPB_5_E1", "classroom": "NPB_5_154"},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert (
        "No route could be found between the selected entrance and destination." in body
    )
    assert "window.routeCoordinates" not in body
    assert "window.floorBounds" not in body
    get_directions.assert_called_once_with("NPB_5_E1", "NPB_5_154")
    get_floor_bounds.assert_not_called()


def test_directions_displays_runtime_error(client, monkeypatch):
    get_directions = Mock(side_effect=RuntimeError("data is unavailable"))
    get_floor_bounds = Mock()
    monkeypatch.setattr(routes, "get_directions", get_directions)
    monkeypatch.setattr(routes, "get_floor_bounds", get_floor_bounds)

    response = client.post(
        "/directions",
        data={"entrance": "NPB_5_E1", "classroom": "NPB_5_154"},
    )

    assert response.status_code == 200
    assert "data is unavailable" in response.get_data(as_text=True)
    get_floor_bounds.assert_not_called()


def test_directions_displays_floor_bounds_runtime_error(client, monkeypatch):
    route = {
        "directions": ["Leave the elevator."],
        "coordinates": [{"x": 1, "y": 2, "floor": 4}],
    }
    monkeypatch.setattr(routes, "get_directions", Mock(return_value=route))
    monkeypatch.setattr(
        routes,
        "get_floor_bounds",
        Mock(side_effect=RuntimeError("floor data is unavailable")),
    )

    response = client.post(
        "/directions",
        data={"entrance": "NPB_5_E1", "classroom": "NPB_5_154"},
    )

    assert response.status_code == 200
    assert "floor data is unavailable" in response.get_data(as_text=True)


def test_directions_does_not_request_floor_bounds_for_empty_coordinates(
    client, monkeypatch
):
    route = {
        "directions": ["The route has no mappable coordinates."],
        "coordinates": [],
    }
    get_floor_bounds = Mock()
    monkeypatch.setattr(routes, "get_directions", Mock(return_value=route))
    monkeypatch.setattr(routes, "get_floor_bounds", get_floor_bounds)

    response = client.post(
        "/directions",
        data={"entrance": "NPB_5_E1", "classroom": "NPB_5_154"},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert embedded_json(body, "directionSteps") == route["directions"]
    assert "window.routeCoordinates" not in body
    assert "window.floorBounds" not in body
    assert "Map will appear here after you select directions" in body
    get_floor_bounds.assert_not_called()


def test_api_test_returns_json_from_pathfinder(client, monkeypatch):
    expected = {"directions": ["Test route"], "coordinates": []}
    get_directions = Mock(return_value=expected)
    monkeypatch.setattr(routes, "get_directions", get_directions)

    response = client.get("/api/test")

    assert response.status_code == 200
    assert response.is_json
    assert response.mimetype == "application/json"
    assert response.get_json() == expected
    get_directions.assert_called_once_with("NPB_5_E1", "NPB_5_154")


def test_unknown_url_returns_not_found(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("path", "mimetype"),
    [
        ("/static/css/styles.css", "text/css"),
        ("/static/js/directions.js", "text/javascript"),
        ("/static/js/map.js", "text/javascript"),
    ],
)
def test_static_assets_are_served(client, path, mimetype):
    response = client.get(path)

    assert response.status_code == 200
    assert response.mimetype == mimetype
    assert response.data
