from flask import Response


def test_health_endpoint(client) -> None:
    response: Response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {}
