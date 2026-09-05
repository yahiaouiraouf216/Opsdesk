"""
Fixtures pytest partagées.

Utilise TestingConfig (voir app/config.py), qui pointe vers
TEST_DATABASE_URL afin de ne jamais modifier la base de développement.
"""

import os

import pytest

os.environ.setdefault("APP_ENV", "testing")

from app import create_app
from app.config import TestingConfig
from app.database import db as _db
from app.models import User, UserRole


@pytest.fixture()
def app():
    application = create_app(TestingConfig)

    with application.app_context():
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def regular_user(app, db):
    user = User(username="testuser", role=UserRole.USER)
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def technician_user(app, db):
    user = User(username="testtech", role=UserRole.TECHNICIAN)
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def logged_in_client(client, regular_user):
    client.post(
        "/login",
        data={"username": "testuser", "password": "testpass123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture()
def logged_in_technician_client(client, technician_user):
    client.post(
        "/login",
        data={"username": "testtech", "password": "testpass123"},
        follow_redirects=True,
    )
    return client
