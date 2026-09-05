def test_health_endpoint_returns_healthy(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
