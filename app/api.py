"""
API REST de OpsDesk.

Endpoints :
    GET    /api/tickets
    GET    /api/tickets/<id>
    POST   /api/tickets
    PUT    /api/tickets/<id>
    DELETE /api/tickets/<id>
    GET    /api/health
"""

import logging

from flask import Blueprint, jsonify, request

from app.auth import get_current_user
from app.database import db
from app.models import Ticket, TicketCategory, TicketPriority, TicketStatus

logger = logging.getLogger("opsdesk")

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _require_api_user():
    """Authentification simple pour l'API, basée sur la session existante.

    Retourne l'utilisateur courant, ou None si non authentifié.
    """
    return get_current_user()


def _validate_ticket_payload(data, partial=False):
    """Valide un payload de création/modification de ticket.

    Retourne (errors: list[str], cleaned: dict).
    """
    errors = []
    cleaned = {}

    title = data.get("title")
    if title is not None:
        title = str(title).strip()
        if not title:
            errors.append("title ne peut pas être vide")
        else:
            cleaned["title"] = title
    elif not partial:
        errors.append("title est requis")

    if "description" in data:
        cleaned["description"] = str(data.get("description") or "").strip()

    category = data.get("category")
    if category is not None:
        if category not in TicketCategory.ALL:
            errors.append(f"category invalide (valeurs: {TicketCategory.ALL})")
        else:
            cleaned["category"] = category

    priority = data.get("priority")
    if priority is not None:
        if priority not in TicketPriority.ALL:
            errors.append(f"priority invalide (valeurs: {TicketPriority.ALL})")
        else:
            cleaned["priority"] = priority

    status = data.get("status")
    if status is not None:
        if status not in TicketStatus.ALL:
            errors.append(f"status invalide (valeurs: {TicketStatus.ALL})")
        else:
            cleaned["status"] = status

    return errors, cleaned


@api_bp.route("/health", methods=["GET"])
def health():
    """Endpoint de health check, utilisé plus tard par l'infrastructure DevOps."""
    return jsonify({"status": "healthy"})


@api_bp.route("/tickets", methods=["GET"])
def list_tickets():
    user = _require_api_user()
    if user is None:
        return jsonify({"error": "authentication required"}), 401

    query = Ticket.query
    if not user.is_technician:
        query = query.filter_by(requester_id=user.id)

    status = request.args.get("status")
    priority = request.args.get("priority")
    category = request.args.get("category")

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tickets])


@api_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    user = _require_api_user()
    if user is None:
        return jsonify({"error": "authentication required"}), 401

    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": "ticket not found"}), 404

    if not user.is_technician and ticket.requester_id != user.id:
        return jsonify({"error": "forbidden"}), 403

    return jsonify(ticket.to_dict())


@api_bp.route("/tickets", methods=["POST"])
def create_ticket():
    user = _require_api_user()
    if user is None:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    errors, cleaned = _validate_ticket_payload(data, partial=False)
    if errors:
        return jsonify({"errors": errors}), 400

    ticket = Ticket(
        title=cleaned["title"],
        description=cleaned.get("description", ""),
        category=cleaned.get("category", TicketCategory.OTHER),
        priority=cleaned.get("priority", TicketPriority.MEDIUM),
        status=TicketStatus.OPEN,
        requester_id=user.id,
    )
    db.session.add(ticket)
    db.session.commit()

    logger.info("API: ticket #%s créé par '%s'", ticket.id, user.username)
    return jsonify(ticket.to_dict()), 201


@api_bp.route("/tickets/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id):
    user = _require_api_user()
    if user is None:
        return jsonify({"error": "authentication required"}), 401

    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": "ticket not found"}), 404

    if not user.is_technician and ticket.requester_id != user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    errors, cleaned = _validate_ticket_payload(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    # Un simple utilisateur ne peut pas changer le statut/priorité de son ticket
    if not user.is_technician:
        cleaned.pop("status", None)
        cleaned.pop("priority", None)

    for field, value in cleaned.items():
        setattr(ticket, field, value)

    db.session.commit()
    logger.info("API: ticket #%s modifié par '%s'", ticket.id, user.username)
    return jsonify(ticket.to_dict())


@api_bp.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    user = _require_api_user()
    if user is None:
        return jsonify({"error": "authentication required"}), 401

    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        return jsonify({"error": "ticket not found"}), 404

    if not user.is_technician and ticket.requester_id != user.id:
        return jsonify({"error": "forbidden"}), 403

    db.session.delete(ticket)
    db.session.commit()
    logger.info("API: ticket #%s supprimé par '%s'", ticket_id, user.username)
    return jsonify({"result": "deleted"})
