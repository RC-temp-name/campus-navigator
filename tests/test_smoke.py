"""Smoke tests: keep CI honest until a real suite exists."""


def test_app_factory_boots():
    """App factory builds without import-time graph loading."""
    from app import create_app

    app = create_app()

    assert app is not None


def test_api_test_route_serves_directions():
    """GET /api/test loads the graph from live data and routes a query."""
    from app import create_app

    client = create_app().test_client()
    resp = client.get("/api/test")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "directions" in data
