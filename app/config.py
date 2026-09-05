"""
Configuration de l'application, entièrement basée sur les variables d'environnement.

Aucun secret n'est codé en dur ici : tout provient de l'environnement,
avec des valeurs par défaut sûres uniquement pour le développement local.
"""

import os


def _str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Configuration de base, commune à tous les environnements."""

    # Base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://username:password@localhost:5432/opsdesk",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sécurité
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")

    # Environnement applicatif : development | testing | production
    APP_ENV = os.environ.get("APP_ENV", "development")

    # Port d'écoute (utilisé par run.py, utile pour la conteneurisation future)
    PORT = int(os.environ.get("PORT", 5000))

    # Débogage Flask (désactivé par défaut, activé seulement en dev explicite)
    DEBUG = _str_to_bool(os.environ.get("FLASK_DEBUG", "false"))


class TestingConfig(Config):
    """Configuration utilisée par la suite de tests pytest.

    Utilise une base de données séparée (TEST_DATABASE_URL) pour ne jamais
    toucher à la base de développement.
    """

    TESTING = True
    APP_ENV = "testing"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://username:password@localhost:5432/opsdesk_test",
    )
    WTF_CSRF_ENABLED = False


def get_config():
    """Retourne la classe de configuration adaptée à APP_ENV."""
    if os.environ.get("APP_ENV") == "testing":
        return TestingConfig
    return Config
