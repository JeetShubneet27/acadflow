from app.models.enums import RoleEnum

from tests.utils import set_user_role, verify_otp


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
    assert response.status_code == 202
    return verify_otp(client, email)


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_permissions_matrix(client):
    owner = _signup(client, "owner@uni.edu", "secret", "Owner")
    owner_token = _login(client, "owner@uni.edu", "secret")
    member = _signup(client, "member@uni.edu", "secret", "Member")
    member_token = _login(client, "member@uni.edu", "secret")
    faculty = _signup(client, "faculty@uni.edu", "secret", "Faculty")
    set_user_role("faculty@uni.edu", RoleEnum.faculty)
    faculty_token = _login(client, "faculty@uni.edu", "secret")

    project = client.post(
        "/projects",
        json={"title": "Permissions", "abstract": "Test", "visibility": "private"},
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

    owner_perm = client.get(
        f"/projects/{project['id']}/permissions",
        headers=_auth_headers(owner_token),
    ).json()
    assert owner_perm["can_invite"] is True
    assert owner_perm["can_manage_members"] is True

    member_perm = client.get(
        f"/projects/{project['id']}/permissions",
        headers=_auth_headers(member_token),
    ).json()
    assert member_perm["can_invite"] is False
    assert member_perm["can_upload_drafts"] is True

    faculty_perm = client.get(
        f"/projects/{project['id']}/permissions",
        headers=_auth_headers(faculty_token),
    ).json()
    assert faculty_perm["can_manage_members"] is True
