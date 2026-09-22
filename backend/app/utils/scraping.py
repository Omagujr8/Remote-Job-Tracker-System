"""
Best-effort metadata extraction from a pasted job-posting URL.

This is intentionally lightweight (no headless browser, no JS execution) so
it has no heavy dependencies and stays within free-tier resource limits.
Many job boards block simple scrapers or render via JS, so this always
degrades gracefully: on any failure, it returns empty fields and a note
telling the user to fill the form in manually rather than raising an error.
"""
import httpx
from bs4 import BeautifulSoup


def extract_job_metadata(url: str) -> dict:
    """
    Attempts to pull a job title and company name from a URL's HTML meta tags
    (og:title, og:site_name, <title>). Returns a dict with best-effort guesses.
    Never raises — always returns a usable (possibly empty) result.
    """
    result = {"job_title": None, "company_name": None, "note": "Parsed successfully."}

    if not url or not url.startswith(("http://", "https://")):
        result["note"] = "Invalid URL — please enter fields manually."
        return result

    try:
        response = httpx.get(
            url,
            timeout=6.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; M4JobTrackerBot/1.0)"},
        )
        response.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        result["note"] = (
            "Couldn't fetch that URL (it may block bots or require login). "
            "The link was still saved — please fill in the other fields manually."
        )
        return result

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        og_title = soup.find("meta", property="og:title")
        title_tag = soup.find("title")
        og_site = soup.find("meta", property="og:site_name")

        job_title = None
        if og_title and og_title.get("content"):
            job_title = og_title["content"].strip()
        elif title_tag and title_tag.text:
            job_title = title_tag.text.strip()

        company_name = None
        if og_site and og_site.get("content"):
            company_name = og_site["content"].strip()

        # Many job titles come through as "Job Title - Company | Board Name".
        # Try to split on common separators to isolate a cleaner title/company.
        if job_title and (" - " in job_title or " | " in job_title):
            for sep in (" | ", " - "):
                if sep in job_title:
                    parts = [p.strip() for p in job_title.split(sep) if p.strip()]
                    if len(parts) >= 2:
                        job_title = parts[0]
                        if not company_name:
                            company_name = parts[1]
                    break

        result["job_title"] = job_title
        result["company_name"] = company_name
        if not job_title and not company_name:
            result["note"] = (
                "Couldn't confidently detect the job title or company from this page. "
                "Please fill them in manually."
            )
    except Exception:
        result["note"] = "Parsed the page but couldn't extract clean metadata — please check the fields."

    return result
