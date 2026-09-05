"""
Instance SQLAlchemy partagée par toute l'application.

Séparée dans son propre module pour éviter les imports circulaires
entre app/__init__.py, app/models.py, app/routes.py et app/api.py.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
