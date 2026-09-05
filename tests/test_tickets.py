import json

from app.models import Ticket, TicketCategory, TicketPriority, TicketStatus


def _login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_create_ticket_via_api(client, regular_user):
    _login(client, "testuser", "testpass123")

    response = client.post(
        "/api/tickets",
        data=json.dumps(
            {
                "title": "Écran cassé",
                "description": "L'écran externe ne s'allume plus.",
                "category": TicketCategory.HARDWARE,
                "priority": TicketPriority.HIGH,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["title"] == "Écran cassé"
    assert payload["status"] == TicketStatus.OPEN
    assert payload["requester"] == "testuser"


def test_create_ticket_without_title_fails(client, regular_user):
    _login(client, "testuser", "testpass123")

    response = client.post(
        "/api/tickets",
        data=json.dumps({"description": "Sans titre"}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "errors" in response.get_json()


def test_list_tickets_returns_only_own_tickets_for_regular_user(client, db, regular_user, technician_user):
    ticket_mine = Ticket(
        title="Mon ticket",
        description="",
        requester_id=regular_user.id,
    )
    ticket_other = Ticket(
        title="Ticket d'un autre",
        description="",
        requester_id=technician_user.id,
    )
    db.session.add_all([ticket_mine, ticket_other])
    db.session.commit()

    _login(client, "testuser", "testpass123")
    response = client.get("/api/tickets")

    assert response.status_code == 200
    titles = [t["title"] for t in response.get_json()]
    assert "Mon ticket" in titles
    assert "Ticket d'un autre" not in titles


def test_update_ticket_title(client, db, regular_user):
    ticket = Ticket(title="Ancien titre", description="", requester_id=regular_user.id)
    db.session.add(ticket)
    db.session.commit()

    _login(client, "testuser", "testpass123")
    response = client.put(
        f"/api/tickets/{ticket.id}",
        data=json.dumps({"title": "Nouveau titre"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json()["title"] == "Nouveau titre"


def test_regular_user_cannot_change_status_via_api(client, db, regular_user):
    ticket = Ticket(title="Ticket", description="", requester_id=regular_user.id)
    db.session.add(ticket)
    db.session.commit()

    _login(client, "testuser", "testpass123")
    response = client.put(
        f"/api/tickets/{ticket.id}",
        data=json.dumps({"status": TicketStatus.RESOLVED}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == TicketStatus.OPEN


def test_technician_can_change_status_via_web_form(client, db, technician_user, regular_user):
    ticket = Ticket(title="Ticket", description="", requester_id=regular_user.id)
    db.session.add(ticket)
    db.session.commit()

    _login(client, "testtech", "testpass123")
    response = client.post(
        f"/tickets/{ticket.id}/status",
        data={"status": TicketStatus.IN_PROGRESS},
        follow_redirects=True,
    )

    assert response.status_code == 200
    refreshed = db.session.get(Ticket, ticket.id)
    assert refreshed.status == TicketStatus.IN_PROGRESS


def test_delete_ticket_via_api(client, db, regular_user):
    ticket = Ticket(title="À supprimer", description="", requester_id=regular_user.id)
    db.session.add(ticket)
    db.session.commit()
    ticket_id = ticket.id

    _login(client, "testuser", "testpass123")
    response = client.delete(f"/api/tickets/{ticket_id}")

    assert response.status_code == 200
    assert db.session.get(Ticket, ticket_id) is None
