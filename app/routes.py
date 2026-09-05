"""
Vues HTML de OpsDesk (rendu de templates Jinja2).

Séparées de l'API REST (app/api.py), qui elle retourne du JSON.
"""

import logging

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app.auth import get_current_user, login_required, technician_required
from app.database import db
from app.models import (
    Comment,
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    User,
    UserRole,
)

logger = logging.getLogger("opsdesk")

routes_bp = Blueprint("routes", __name__)


@routes_bp.route("/")
def index():
    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()

    base_query = Ticket.query
    if not user.is_technician:
        base_query = base_query.filter_by(requester_id=user.id)

    total = base_query.count()
    open_count = base_query.filter_by(status=TicketStatus.OPEN).count()
    in_progress_count = base_query.filter_by(status=TicketStatus.IN_PROGRESS).count()
    critical_count = base_query.filter_by(priority=TicketPriority.CRITICAL).count()
    resolved_count = base_query.filter_by(status=TicketStatus.RESOLVED).count()

    by_priority = dict(
        base_query.with_entities(Ticket.priority, func.count(Ticket.id))
        .group_by(Ticket.priority)
        .all()
    )
    by_status = dict(
        base_query.with_entities(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )
    by_category = dict(
        base_query.with_entities(Ticket.category, func.count(Ticket.id))
        .group_by(Ticket.category)
        .all()
    )

    recent_tickets = base_query.order_by(Ticket.created_at.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total=total,
        open_count=open_count,
        in_progress_count=in_progress_count,
        critical_count=critical_count,
        resolved_count=resolved_count,
        by_priority=by_priority,
        by_status=by_status,
        by_category=by_category,
        recent_tickets=recent_tickets,
        statuses=TicketStatus.ALL,
        priorities=TicketPriority.ALL,
        categories=TicketCategory.ALL,
    )


@routes_bp.route("/tickets")
@login_required
def ticket_list():
    user = get_current_user()

    query = Ticket.query
    if not user.is_technician:
        query = query.filter_by(requester_id=user.id)

    title_filter = request.args.get("title", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    category_filter = request.args.get("category", "").strip()
    technician_filter = request.args.get("technician", "").strip()

    if title_filter:
        query = query.filter(Ticket.title.ilike(f"%{title_filter}%"))
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if technician_filter:
        query = query.join(User, Ticket.assignee_id == User.id).filter(
            User.username.ilike(f"%{technician_filter}%")
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    technicians = User.query.filter_by(role=UserRole.TECHNICIAN).all()

    return render_template(
        "tickets.html",
        tickets=tickets,
        technicians=technicians,
        statuses=TicketStatus.ALL,
        priorities=TicketPriority.ALL,
        categories=TicketCategory.ALL,
        filters={
            "title": title_filter,
            "status": status_filter,
            "priority": priority_filter,
            "category": category_filter,
            "technician": technician_filter,
        },
    )


@routes_bp.route("/tickets/new", methods=["GET", "POST"])
@login_required
def ticket_new():
    user = get_current_user()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", TicketCategory.OTHER)
        priority = request.form.get("priority", TicketPriority.MEDIUM)

        if not title:
            flash("Le titre est obligatoire.", "danger")
            return render_template(
                "ticket_form.html",
                categories=TicketCategory.ALL,
                priorities=TicketPriority.ALL,
                ticket=None,
            )

        if category not in TicketCategory.ALL:
            category = TicketCategory.OTHER
        if priority not in TicketPriority.ALL:
            priority = TicketPriority.MEDIUM

        ticket = Ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=TicketStatus.OPEN,
            requester_id=user.id,
        )
        db.session.add(ticket)
        db.session.commit()

        logger.info("Ticket #%s créé par '%s'", ticket.id, user.username)
        flash("Ticket créé avec succès.", "success")
        return redirect(url_for("routes.ticket_detail", ticket_id=ticket.id))

    return render_template(
        "ticket_form.html",
        categories=TicketCategory.ALL,
        priorities=TicketPriority.ALL,
        ticket=None,
    )


@routes_bp.route("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    user = get_current_user()
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    if not user.is_technician and ticket.requester_id != user.id:
        abort(403)

    technicians = User.query.filter_by(role=UserRole.TECHNICIAN).all()

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        technicians=technicians,
        statuses=TicketStatus.ALL,
        priorities=TicketPriority.ALL,
    )


@routes_bp.route("/tickets/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def ticket_edit(ticket_id):
    user = get_current_user()
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    if not user.is_technician and ticket.requester_id != user.id:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", ticket.category)
        priority = request.form.get("priority", ticket.priority)

        if not title:
            flash("Le titre est obligatoire.", "danger")
            return render_template(
                "ticket_form.html",
                categories=TicketCategory.ALL,
                priorities=TicketPriority.ALL,
                ticket=ticket,
            )

        ticket.title = title
        ticket.description = description
        if category in TicketCategory.ALL:
            ticket.category = category
        if priority in TicketPriority.ALL:
            ticket.priority = priority

        db.session.commit()
        logger.info("Ticket #%s modifié par '%s'", ticket.id, user.username)
        flash("Ticket mis à jour.", "success")
        return redirect(url_for("routes.ticket_detail", ticket_id=ticket.id))

    return render_template(
        "ticket_form.html",
        categories=TicketCategory.ALL,
        priorities=TicketPriority.ALL,
        ticket=ticket,
    )


@routes_bp.route("/tickets/<int:ticket_id>/delete", methods=["POST"])
@login_required
def ticket_delete(ticket_id):
    user = get_current_user()
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    if not user.is_technician and ticket.requester_id != user.id:
        abort(403)

    db.session.delete(ticket)
    db.session.commit()
    logger.info("Ticket #%s supprimé par '%s'", ticket_id, user.username)
    flash("Ticket supprimé.", "info")
    return redirect(url_for("routes.ticket_list"))


@routes_bp.route("/tickets/<int:ticket_id>/status", methods=["POST"])
@technician_required
def ticket_change_status(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    new_status = request.form.get("status")
    if new_status in TicketStatus.ALL:
        ticket.status = new_status
        db.session.commit()
        logger.info("Ticket #%s -> statut '%s'", ticket.id, new_status)
        flash("Statut mis à jour.", "success")
    else:
        flash("Statut invalide.", "danger")

    return redirect(url_for("routes.ticket_detail", ticket_id=ticket_id))


@routes_bp.route("/tickets/<int:ticket_id>/priority", methods=["POST"])
@technician_required
def ticket_change_priority(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    new_priority = request.form.get("priority")
    if new_priority in TicketPriority.ALL:
        ticket.priority = new_priority
        db.session.commit()
        logger.info("Ticket #%s -> priorité '%s'", ticket.id, new_priority)
        flash("Priorité mise à jour.", "success")
    else:
        flash("Priorité invalide.", "danger")

    return redirect(url_for("routes.ticket_detail", ticket_id=ticket_id))


@routes_bp.route("/tickets/<int:ticket_id>/assign", methods=["POST"])
@technician_required
def ticket_assign(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    technician_id = request.form.get("technician_id")
    if technician_id:
        technician = db.session.get(User, int(technician_id))
        if technician is not None and technician.is_technician:
            ticket.assignee_id = technician.id
            db.session.commit()
            logger.info("Ticket #%s assigné à '%s'", ticket.id, technician.username)
            flash(f"Ticket assigné à {technician.username}.", "success")
        else:
            flash("Technicien invalide.", "danger")
    else:
        ticket.assignee_id = None
        db.session.commit()
        flash("Assignation retirée.", "info")

    return redirect(url_for("routes.ticket_detail", ticket_id=ticket_id))


@routes_bp.route("/tickets/<int:ticket_id>/comments", methods=["POST"])
@login_required
def add_comment(ticket_id):
    user = get_current_user()
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    if not user.is_technician and ticket.requester_id != user.id:
        abort(403)

    content = request.form.get("content", "").strip()
    if not content:
        flash("Le commentaire ne peut pas être vide.", "danger")
        return redirect(url_for("routes.ticket_detail", ticket_id=ticket_id))

    comment = Comment(ticket_id=ticket.id, author_id=user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    logger.info("Commentaire ajouté sur le ticket #%s par '%s'", ticket.id, user.username)

    return redirect(url_for("routes.ticket_detail", ticket_id=ticket_id))
