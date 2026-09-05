"""
Application factory pour OpsDesk.

Centralise :
- la configuration du logging (stdout/stderr)
- l'initialisation de SQLAlchemy
- l'enregistrement des blueprints (auth, routes, api)
- la création des tables et l'insertion des données de démonstration
"""

import logging
import os
import sys

from flask import Flask

from app.config import get_config
from app.database import db


def configure_logging(app: Flask) -> None:
    """Configure des logs simples, écrits vers stdout.

    Format volontairement simple, lisible par un humain en développement,
    et facilement redirigeable vers Docker/CloudWatch plus tard sans
    modification de code.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("opsdesk")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

    # Réduit le bruit des logs SQLAlchemy/Werkzeug en dehors du debug
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def seed_demo_data() -> None:
    """Insère des données de démonstration si la base est vide.

    Idempotent : n'insère rien si des utilisateurs existent déjà,
    afin de ne jamais écraser des données réelles au redémarrage.
    """
    from app.models import Comment, Ticket, TicketCategory, TicketPriority, TicketStatus, User, UserRole

    logger = logging.getLogger("opsdesk")

    if User.query.first() is not None:
        logger.info("Données existantes détectées, seed ignoré.")
        return

    logger.info("Base vide détectée, insertion des données de démonstration...")

    alice = User(username="alice", role=UserRole.USER)
    alice.set_password("password123")

    bob = User(username="bob", role=UserRole.USER)
    bob.set_password("password123")

    tania = User(username="tania.tech", role=UserRole.TECHNICIAN)
    tania.set_password("password123")

    marc = User(username="marc.tech", role=UserRole.TECHNICIAN)
    marc.set_password("password123")

    db.session.add_all([alice, bob, tania, marc])
    db.session.flush()  # pour obtenir les IDs avant de créer les tickets

    tickets = [
        Ticket(
            title="Ordinateur qui ne démarre plus",
            description="Écran noir au démarrage depuis ce matin, aucun bip.",
            category=TicketCategory.HARDWARE,
            priority=TicketPriority.HIGH,
            status=TicketStatus.OPEN,
            requester_id=alice.id,
            assignee_id=tania.id,
        ),
        Ticket(
            title="Problème de connexion VPN",
            description="Impossible de se connecter au VPN depuis hier soir.",
            category=TicketCategory.NETWORK,
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.IN_PROGRESS,
            requester_id=bob.id,
            assignee_id=marc.id,
        ),
        Ticket(
            title="Accès refusé à l'application comptabilité",
            description="Le message 'Accès refusé' apparaît depuis la mise à jour.",
            category=TicketCategory.ACCESS,
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.OPEN,
            requester_id=alice.id,
        ),
        Ticket(
            title="Mot de passe oublié",
            description="Demande de réinitialisation du mot de passe Windows.",
            category=TicketCategory.SECURITY,
            priority=TicketPriority.LOW,
            status=TicketStatus.RESOLVED,
            requester_id=bob.id,
            assignee_id=tania.id,
        ),
        Ticket(
            title="Installation de logiciel de design",
            description="Besoin d'Adobe Acrobat Pro installé sur le poste.",
            category=TicketCategory.SOFTWARE,
            priority=TicketPriority.LOW,
            status=TicketStatus.WAITING,
            requester_id=alice.id,
            assignee_id=marc.id,
        ),
        Ticket(
            title="Alerte antivirus suspecte",
            description="L'antivirus a bloqué un fichier téléchargé par email.",
            category=TicketCategory.SECURITY,
            priority=TicketPriority.CRITICAL,
            status=TicketStatus.IN_PROGRESS,
            requester_id=bob.id,
            assignee_id=tania.id,
        ),
        Ticket(
            title="Lenteur réseau au 2e étage",
            description="Le réseau est très lent depuis ce matin au 2e étage.",
            category=TicketCategory.NETWORK,
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.CLOSED,
            requester_id=alice.id,
            assignee_id=marc.id,
        ),
    ]
    db.session.add_all(tickets)
    db.session.flush()

    comments = [
        Comment(ticket_id=tickets[0].id, author_id=tania.id, content="Prise en charge, je passe voir le poste."),
        Comment(ticket_id=tickets[0].id, author_id=alice.id, content="Merci, je suis à mon bureau toute la journée."),
        Comment(ticket_id=tickets[1].id, author_id=marc.id, content="Vérification des identifiants VPN en cours."),
        Comment(ticket_id=tickets[5].id, author_id=tania.id, content="Fichier mis en quarantaine, analyse en cours."),
    ]
    db.session.add_all(comments)

    db.session.commit()
    logger.info("Seed terminé : %s utilisateurs, %s tickets, %s commentaires.",
                4, len(tickets), len(comments))


def create_app(config_class=None) -> Flask:
    """Application factory."""
    # templates/ et static/ vivent à la racine du projet, pas dans app/,
    # donc on pointe explicitement Flask vers ces dossiers.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )
    app.config.from_object(config_class or get_config())

    configure_logging(app)
    logger = logging.getLogger("opsdesk")
    logger.info("Démarrage de OpsDesk (APP_ENV=%s)", app.config.get("APP_ENV"))

    db.init_app(app)

    from app.auth import auth_bp
    from app.routes import routes_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_current_user():
        from app.auth import get_current_user
        return {"current_user": get_current_user()}

    @app.errorhandler(404)
    def not_found(_error):
        return {"error": "not found"}, 404

    @app.errorhandler(403)
    def forbidden(_error):
        return {"error": "forbidden"}, 403

    @app.errorhandler(500)
    def server_error(error):
        logger.error("Erreur serveur: %s", error)
        return {"error": "internal server error"}, 500

    with app.app_context():
        db.create_all()
        if not app.config.get("TESTING"):
            seed_demo_data()

    return app
