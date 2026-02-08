from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.enums import InviteStatus, RoleEnum
from app.models.project_invite import ProjectInvite

from tests.utils import set_user_role


def _signup(client, email: str, password: str, full_name: str):
    response = client.post(
        "/signup",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def _login(client, email: str, password: str):
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_invite_lifecycle(client):
    _signup(client, "owner@example.edu", "secret", "Owner")
    set_user_role("owner@example.edu", RoleEnum.faculty)
    owner_token = _login(client, "owner@example.edu", "secret")

    student = _signup(client, "student@example.edu", "secret", "Student")
    student_token = _login(client, "student@example.edu", "secret")

    project = client.post(
        "/projects",
        json={"title": "Invites", "abstract": "Test", "visibility": "private"},
        headers=_auth_headers(owner_token),
    ).json()

    invite = client.post(
        f"/projects/{project['id']}/invite",
        json={"invitee_id": student["id"], "membership_role": "coauthor"},
        headers=_auth_headers(owner_token),
    ).json()

    db = SessionLocal()
    try:
        db_invite = db.query(ProjectInvite).get(invite["id"])
        db_invite.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    invites = client.get(
        f"/projects/{project['id']}/invites",
        headers=_auth_headers(owner_token),
    ).json()
    assert invites[0]["status"] == InviteStatus.expired.value

    resent = client.post(
        f"/projects/invites/{invite['id']}/resend",
        headers=_auth_headers(owner_token),
    ).json()
    assert resent["status"] == InviteStatus.pending.value

    revoked = client.delete(
        f"/projects/invites/{invite['id']}",
        headers=_auth_headers(owner_token),
    ).json()
    assert revoked["status"] == InviteStatus.revoked.value

    invitee_response = client.get("/projects/invites", headers=_auth_headers(student_token))
    assert invitee_response.status_code == 200
    invitee_view = invitee_response.json()
    assert isinstance(invitee_view, list)
    assert any(inv["status"] == InviteStatus.revoked.value for inv in invitee_view)
