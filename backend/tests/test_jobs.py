from tests.conftest import register_and_login


def make_job_payload(**overrides):
    payload = {
        "job_title": "Backend Engineer",
        "company_name": "Acme Corp",
        "status": "applied",
        "application_date": "2026-09-01",
        "salary_range": "$100k-120k",
        "location": "Remote",
        "contact_info": "recruiter@acme.com",
        "interview_notes": "",
        "job_url": "https://example.com/job/123",
        "referred_by": "",
        "tag_names": ["dream-job", "urgent"],
    }
    payload.update(overrides)
    return payload


def test_create_job_success(client):
    headers = register_and_login(client)
    resp = client.post("/jobs", json=make_job_payload(), headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["job_title"] == "Backend Engineer"
    assert body["status"] == "applied"
    assert len(body["tags"]) == 2
    assert body["is_archived"] is False
    assert "days_since_update" in body


def test_create_job_missing_required_field_rejected(client):
    headers = register_and_login(client)
    payload = make_job_payload()
    del payload["job_title"]
    resp = client.post("/jobs", json=payload, headers=headers)
    assert resp.status_code == 422


def test_create_job_invalid_status_rejected(client):
    headers = register_and_login(client)
    payload = make_job_payload(status="not_a_real_status")
    resp = client.post("/jobs", json=payload, headers=headers)
    assert resp.status_code == 422


def test_create_job_invalid_date_rejected(client):
    headers = register_and_login(client)
    payload = make_job_payload(application_date="not-a-date")
    resp = client.post("/jobs", json=payload, headers=headers)
    assert resp.status_code == 422


def test_duplicate_detection_blocks_second_create(client):
    headers = register_and_login(client)
    client.post("/jobs", json=make_job_payload(), headers=headers)
    resp = client.post("/jobs", json=make_job_payload(), headers=headers)
    assert resp.status_code == 409
    assert "existing_job_id" in resp.json()["detail"]


def test_duplicate_force_create_bypasses_warning(client):
    headers = register_and_login(client)
    client.post("/jobs", json=make_job_payload(), headers=headers)
    resp = client.post("/jobs", json=make_job_payload(force_create=True), headers=headers)
    assert resp.status_code == 201


def test_check_duplicate_endpoint(client):
    headers = register_and_login(client)
    client.post("/jobs", json=make_job_payload(), headers=headers)
    resp = client.get(
        "/jobs/check-duplicate",
        params={"company_name": "Acme Corp", "job_title": "Backend Engineer"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["duplicate_found"] is True


def test_list_jobs_returns_only_own_jobs(client):
    headers1 = register_and_login(client, "u1@example.com")
    headers2 = register_and_login(client, "u2@example.com")

    client.post("/jobs", json=make_job_payload(company_name="Company A"), headers=headers1)
    client.post("/jobs", json=make_job_payload(company_name="Company B"), headers=headers2)

    resp1 = client.get("/jobs", headers=headers1)
    resp2 = client.get("/jobs", headers=headers2)

    assert len(resp1.json()) == 1
    assert resp1.json()[0]["company_name"] == "Company A"
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["company_name"] == "Company B"


def test_user_cannot_access_another_users_job(client):
    headers1 = register_and_login(client, "owner@example.com")
    headers2 = register_and_login(client, "intruder@example.com")

    created = client.post("/jobs", json=make_job_payload(), headers=headers1).json()
    job_id = created["id"]

    resp = client.get(f"/jobs/{job_id}", headers=headers2)
    assert resp.status_code == 404  # not 403 — avoids leaking existence


def test_user_cannot_update_another_users_job(client):
    headers1 = register_and_login(client, "owner2@example.com")
    headers2 = register_and_login(client, "intruder2@example.com")

    created = client.post("/jobs", json=make_job_payload(), headers=headers1).json()
    job_id = created["id"]

    resp = client.patch(f"/jobs/{job_id}", json={"job_title": "Hacked Title"}, headers=headers2)
    assert resp.status_code == 404


def test_user_cannot_delete_another_users_job(client):
    headers1 = register_and_login(client, "owner3@example.com")
    headers2 = register_and_login(client, "intruder3@example.com")

    created = client.post("/jobs", json=make_job_payload(), headers=headers1).json()
    job_id = created["id"]

    resp = client.delete(f"/jobs/{job_id}", headers=headers2)
    assert resp.status_code == 404

    # Confirm it still exists for the real owner
    resp_owner = client.get(f"/jobs/{job_id}", headers=headers1)
    assert resp_owner.status_code == 200


def test_get_nonexistent_job_returns_404(client):
    headers = register_and_login(client)
    resp = client.get("/jobs/99999", headers=headers)
    assert resp.status_code == 404


def test_update_job_partial_fields(client):
    headers = register_and_login(client)
    created = client.post("/jobs", json=make_job_payload(), headers=headers).json()
    resp = client.patch(
        f"/jobs/{created['id']}", json={"location": "Onsite - NYC"}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["location"] == "Onsite - NYC"
    assert body["job_title"] == "Backend Engineer"  # untouched fields preserved


def test_status_update_endpoint(client):
    headers = register_and_login(client)
    created = client.post("/jobs", json=make_job_payload(), headers=headers).json()
    resp = client.patch(
        f"/jobs/{created['id']}/status", json={"status": "phone_screen"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "phone_screen"


def test_status_update_invalid_value_rejected(client):
    headers = register_and_login(client)
    created = client.post("/jobs", json=make_job_payload(), headers=headers).json()
    resp = client.patch(
        f"/jobs/{created['id']}/status", json={"status": "bogus"}, headers=headers
    )
    assert resp.status_code == 422


def test_archive_and_unarchive_job(client):
    headers = register_and_login(client)
    created = client.post("/jobs", json=make_job_payload(), headers=headers).json()
    job_id = created["id"]

    resp = client.patch(f"/jobs/{job_id}/archive", params={"archived": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_archived"] is True

    # Archived jobs excluded from default list
    listing = client.get("/jobs", headers=headers).json()
    assert len(listing) == 0

    # But visible when explicitly requested
    listing_all = client.get("/jobs", params={"include_archived": True}, headers=headers).json()
    assert len(listing_all) == 1

    resp2 = client.patch(f"/jobs/{job_id}/archive", params={"archived": False}, headers=headers)
    assert resp2.json()["is_archived"] is False


def test_delete_job(client):
    headers = register_and_login(client)
    created = client.post("/jobs", json=make_job_payload(), headers=headers).json()
    job_id = created["id"]

    resp = client.delete(f"/jobs/{job_id}", headers=headers)
    assert resp.status_code == 204

    resp2 = client.get(f"/jobs/{job_id}", headers=headers)
    assert resp2.status_code == 404


def test_filter_by_status(client):
    headers = register_and_login(client)
    client.post("/jobs", json=make_job_payload(company_name="A"), headers=headers)
    j2 = client.post("/jobs", json=make_job_payload(company_name="B"), headers=headers).json()
    client.patch(f"/jobs/{j2['id']}/status", json={"status": "offer"}, headers=headers)

    resp = client.get("/jobs", params={"status_filter": "offer"}, headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["company_name"] == "B"


def test_search_by_keyword(client):
    headers = register_and_login(client)
    client.post(
        "/jobs",
        json=make_job_payload(job_title="Senior Python Developer", company_name="Zeta"),
        headers=headers,
    )
    client.post(
        "/jobs", json=make_job_payload(job_title="Frontend Engineer", company_name="Gamma"), headers=headers
    )
    resp = client.get("/jobs", params={"search": "python"}, headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["company_name"] == "Zeta"


def test_filter_by_tag(client):
    headers = register_and_login(client)
    client.post(
        "/jobs",
        json=make_job_payload(company_name="TagCo", tag_names=["referral"]),
        headers=headers,
    )
    client.post(
        "/jobs",
        json=make_job_payload(company_name="OtherCo", tag_names=["cold-apply"]),
        headers=headers,
    )
    resp = client.get("/jobs", params={"tag": "referral"}, headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["company_name"] == "TagCo"


def test_quick_add_from_url_never_fails_hard(client):
    headers = register_and_login(client)
    resp = client.post(
        "/jobs/quick-add-from-url",
        json={"url": "https://this-domain-should-not-resolve-xyz123.invalid/job/1"},
        headers=headers,
    )
    # Should degrade gracefully, never 500
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_url"] == "https://this-domain-should-not-resolve-xyz123.invalid/job/1"
    assert "note" in body


def test_analytics_endpoint(client):
    headers = register_and_login(client)
    client.post("/jobs", json=make_job_payload(company_name="A"), headers=headers)
    j2 = client.post("/jobs", json=make_job_payload(company_name="B"), headers=headers).json()
    client.patch(f"/jobs/{j2['id']}/status", json={"status": "offer"}, headers=headers)

    resp = client.get("/analytics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_applications"] == 2
    assert body["offer_rate"] == 50.0


def test_csv_export(client):
    headers = register_and_login(client)
    client.post("/jobs", json=make_job_payload(), headers=headers)
    resp = client.get("/export/csv", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Backend Engineer" in resp.text
