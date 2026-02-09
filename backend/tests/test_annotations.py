import io

from tests.utils import verify_otp


def _signup(client, email: str, password: str, full_name: str):
    response = client.post(
        "/signup",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201
    verify_otp(client, email)
    return response.json()


def _login(client, email: str, password: str):
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_annotation_flow(client):
    owner = _signup(client, "owner@dept.edu", "secret", "Owner")
    owner_token = _login(client, "owner@dept.edu", "secret")

    project = client.post(
        "/projects",
        json={"title": "Annotations", "abstract": "Test", "visibility": "private"},
        headers=_auth_headers(owner_token),
    ).json()

    file_payload = {"file": ("draft.pdf", io.BytesIO(b"draft-1"), "application/pdf")}
    draft = client.post(
        f"/projects/{project['id']}/drafts",
        files=file_payload,
        headers=_auth_headers(owner_token),
    ).json()

    annotation = client.post(
        f"/drafts/{draft['id']}/annotations",
        json={"anchor_type": "page", "anchor_data": {"page": 1}, "body": "Check intro"},
        headers=_auth_headers(owner_token),
    )
    assert annotation.status_code == 201
    annotation_id = annotation.json()["id"]

    reply = client.post(
        f"/annotations/{annotation_id}/replies",
        json={"body": "Will revise."},
        headers=_auth_headers(owner_token),
    )
    assert reply.status_code == 201

    resolved = client.post(
        f"/annotations/{annotation_id}/resolve",
        headers=_auth_headers(owner_token),
    )
    assert resolved.json()["status"] == "resolved"

    reopened = client.post(
        f"/annotations/{annotation_id}/reopen",
        headers=_auth_headers(owner_token),
    )
    assert reopened.json()["status"] == "open"
