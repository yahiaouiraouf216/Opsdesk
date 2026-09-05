"""
Modèles de données de OpsDesk.

Trois entités principales :
- User        : utilisateurs de l'application (rôle "user" ou "technician")
- Ticket      : tickets de support IT
- Comment     : commentaires attachés à un ticket
"""

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db


# --- Constantes métier -----------------------------------------------------

class TicketStatus:
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    WAITING = "Waiting"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

    ALL = [OPEN, IN_PROGRESS, WAITING, RESOLVED, CLOSED]


class TicketPriority:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    ALL = [LOW, MEDIUM, HIGH, CRITICAL]


class TicketCategory:
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    ACCESS = "Access"
    SECURITY = "Security"
    OTHER = "Other"

    ALL = [HARDWARE, SOFTWARE, NETWORK, ACCESS, SECURITY, OTHER]


class UserRole:
    USER = "user"
    TECHNICIAN = "technician"

    ALL = [USER, TECHNICIAN]


# --- Modèles -----------------------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.USER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Tickets créés par cet utilisateur (en tant que demandeur)
    requested_tickets = db.relationship(
        "Ticket",
        back_populates="requester",
        foreign_keys="Ticket.requester_id",
    )

    # Tickets assignés à cet utilisateur (s'il est technicien)
    assigned_tickets = db.relationship(
        "Ticket",
        back_populates="assignee",
        foreign_keys="Ticket.assignee_id",
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_technician(self) -> bool:
        return self.role == UserRole.TECHNICIAN

    def to_public_dict(self) -> dict:
        """Représentation sûre de l'utilisateur (jamais de password_hash)."""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")

    category = db.Column(db.String(30), nullable=False, default=TicketCategory.OTHER)
    priority = db.Column(db.String(20), nullable=False, default=TicketPriority.MEDIUM)
    status = db.Column(db.String(20), nullable=False, default=TicketStatus.OPEN)

    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    requester = db.relationship(
        "User", back_populates="requested_tickets", foreign_keys=[requester_id]
    )
    assignee = db.relationship(
        "User", back_populates="assigned_tickets", foreign_keys=[assignee_id]
    )

    comments = db.relationship(
        "Comment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "requester": self.requester.username if self.requester else None,
            "assignee": self.assignee.username if self.assignee else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Ticket #{self.id} {self.title!r} [{self.status}]>"


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    ticket = db.relationship("Ticket", back_populates="comments")
    author = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "author": self.author.username if self.author else None,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Comment #{self.id} on Ticket #{self.ticket_id}>"
