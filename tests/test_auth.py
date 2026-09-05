def test_login_with_valid_credentials_succeeds(client, regular_user):
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpass123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Bienvenue" in response.data or b"dashboard" in response.request.path.encode()


def test_login_with_invalid_password_fails(client, regular_user):
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_with_unknown_username_fails(client):
    response = client.post(
        "/login",
        data={"username": "ghost", "password": "whatever"},
    )

    assert response.status_code == 401


def test_logout_clears_session(logged_in_client):
    response = logged_in_client.get("/logout", follow_redirects=True)

    assert response.status_code == 200

    # Une page protégée doit maintenant rediriger vers /login
    protected_response = logged_in_client.get("/dashboard", follow_redirects=False)
    assert protected_response.status_code == 302
    assert "/login" in protected_response.headers["Location"]


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
