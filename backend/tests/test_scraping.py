import httpx

from app.utils import scraping


def mock_response(monkeypatch, html):
    response = httpx.Response(
        200,
        text=html,
        request=httpx.Request("GET", "https://jobs.example.com/posting"),
    )
    monkeypatch.setattr(scraping.httpx, "get", lambda *args, **kwargs: response)


def test_extract_job_metadata_reports_when_only_a_title_was_found(monkeypatch):
    mock_response(monkeypatch, "<html><head><title>Careers</title></head><body></body></html>")

    result = scraping.extract_job_metadata("https://jobs.example.com/posting")

    assert result["job_title"] == "Careers"
    assert result["company_name"] is None
    assert "couldn't detect the company" in result["note"]


def test_extract_job_metadata_does_not_claim_success_without_fields(monkeypatch):
    mock_response(monkeypatch, "<html><head></head><body></body></html>")

    result = scraping.extract_job_metadata("https://jobs.example.com/posting")

    assert result["job_title"] is None
    assert result["company_name"] is None
    assert "couldn't confidently detect" in result["note"].lower()
