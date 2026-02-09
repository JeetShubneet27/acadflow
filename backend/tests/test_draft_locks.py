import io

from tests.utils import get_user_id, verify_otp

def _signup(client, email: str, password: str, full_name: str):
    response = client.post(
        "/signup",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201
    verify_otp(client, email)
    return {"id": get_user_id(email)}


def _login(client, email: str, password: str):
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_draft_lock_conflict(client):
    owner = _signup(client, "owner@lab.edu", "secret", "Owner")
    owner_token = _login(client, "owner@lab.edu", "secret")

    member = _signup(client, "member@lab.edu", "secret", "Member")
    member_token = _login(client, "member@lab.edu", "secret")

    project = client.post(
        "/projects",
        json={"title": "Drafts", "abstract": "Test", "visibility": "private"},
        headers=_auth_headers(owner_token),
    ).json()

    invite = client.post(
        f"/projects/{project['id']}/invite",
        json={"invitee_id": member["id"], "membership_role": "coauthor"},
        headers=_auth_headers(owner_token),
    ).json()

    client.put(
        f"/projects/invites/{invite['id']}",
        json={"status": "accepted"},
        headers=_auth_headers(member_token),
    )

    file_payload = {"file": ("draft.pdf", io.BytesIO(b"draft-1"), "application/pdf")}
    upload = client.post(
        f"/projects/{project['id']}/drafts",
        files=file_payload,
        headers=_auth_headers(owner_token),
    )
    assert upload.status_code == 201
    draft_id = upload.json()["id"]

    lock = client.post(
        f"/drafts/{draft_id}/lock",
        headers=_auth_headers(owner_token),
    )
    assert lock.status_code == 201

    file_payload = {"file": ("draft2.pdf", io.BytesIO(b"draft-2"), "application/pdf")}
    upload_member = client.post(
        f"/projects/{project['id']}/drafts",
        files=file_payload,
        headers=_auth_headers(member_token),
    )
    assert upload_member.status_code == 409
