"""
Authentification simple par session pour OpsDesk.

Pas de JWT ni d'OAuth : une session Flask classique suffit pour une
application interne. Les mots de passe sont hashés avec Werkzeug
(PBKDF2 + sel), jamais stockés ni renvoyés en clair.
"""

import logging
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.database import db
from app.models import User

logger = logging.getLogger("opsdesk")

auth_bp = Blueprint("auth", __name__)


def get_current_user():
    """Retourne l'objet User connecté, ou None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def login_required(view_func):
    """Exige qu'un utilisateur soit connecté."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)

    return wrapped


def technician_required(view_func):
    """Exige qu'un utilisateur soit connecté ET soit technicien."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if not user.is_technician:
            flash("Accès réservé aux techniciens.", "danger")
            return redirect(url_for("routes.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user() is not None:
        return redirect(url_for("routes.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            logger.warning("Tentative de connexion échouée pour '%s'", username)
            flash("Identifiants invalides.", "danger")
            return render_template("login.html"), 401

        session["user_id"] = user.id
        logger.info("Connexion réussie: utilisateur '%s' (%s)", user.username, user.role)
        flash(f"Bienvenue, {user.username} !", "success")

        next_url = request.args.get("next")
        return redirect(next_url or url_for("routes.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    user = get_current_user()
    if user is not None:
        logger.info("Déconnexion de l'utilisateur '%s'", user.username)
    session.pop("user_id", None)
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login"))
