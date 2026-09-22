import io

from tests.conftest import register_and_login
from tests.test_jobs import make_job_payload


def test_tags_are_isolated_per_user(client):
    headers1 = register_and_login(client, "tagowner1@example.com")
    headers2 = register_and_login(client, "tagowner2@example.com")

    client.post("/jobs", json=make_job_payload(tag_names=["private-tag"]), headers=headers1)

    tags_user1 = client.get("/tags", headers=headers1).json()
    tags_user2 = client.get("/tags", headers=headers2).json()

    assert len(tags_user1) == 1
    assert len(tags_user2) == 0  # user2 must not see user1's tags


def test_analytics_isolated_per_user(client):
    headers1 = register_and_login(client, "analytics1@example.com")
    headers2 = register_and_login(client, "analytics2@example.com")

    client.post("/jobs", json=make_job_payload(company_name="Analytics Co A"), headers=headers1)
    client.post("/jobs", json=make_job_payload(company_name="Analytics Co B"), headers=headers1)
    client.post("/jobs", json=make_job_payload(company_name="Analytics Co C"), headers=headers2)

    a1 = client.get("/analytics", headers=headers1).json()
    a2 = client.get("/analytics", headers=headers2).json()

    assert a1["total_applications"] == 2
    assert a2["total_applications"] == 1


def test_attachment_upload_and_download(client):
    headers = register_and_login(client, "attach@example.com")
    job = client.post("/jobs", json=make_job_payload(), headers=headers).json()

    file_content = b"fake resume content"
    resp = client.post(
        f"/jobs/{job['id']}/attachments",
        files={"file": ("resume.pdf", io.BytesIO(file_content), "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    attachment = resp.json()
    assert attachment["filename"] == "resume.pdf"

    download = client.get(attachment["url"], headers=headers)
    assert download.status_code == 200
    assert download.content == file_content


def test_attachment_isolated_between_users(client):
    headers1 = register_and_login(client, "attachowner@example.com")
    headers2 = register_and_login(client, "attachintruder@example.com")

    job = client.post("/jobs", json=make_job_payload(), headers=headers1).json()
    upload = client.post(
        f"/jobs/{job['id']}/attachments",
        files={"file": ("secret.pdf", io.BytesIO(b"secret content"), "application/pdf")},
        headers=headers1,
    ).json()

    # user2 cannot list attachments on user1's job (job itself is invisible)
    resp = client.get(f"/jobs/{job['id']}/attachments", headers=headers2)
    assert resp.status_code == 404

    # user2 cannot download user1's attachment directly by ID either
    resp2 = client.get(f"/attachments/{upload['id']}/download", headers=headers2)
    assert resp2.status_code == 404


def test_empty_file_upload_rejected(client):
    headers = register_and_login(client, "emptyfile@example.com")
    job = client.post("/jobs", json=make_job_payload(), headers=headers).json()

    resp = client.post(
        f"/jobs/{job['id']}/attachments",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 400


def test_digest_endpoint_requires_correct_secret(client):
    resp = client.post("/digest/send-weekly", headers={"x-digest-secret": "wrong-secret"})
    assert resp.status_code == 401
