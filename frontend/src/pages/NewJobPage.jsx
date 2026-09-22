import { useState } from "react";
import { useNavigate } from "react-router-dom";
import JobForm, { buildInitialForm } from "../components/JobForm";
import { api, ApiError } from "../api/client";
import "./NewJobPage.css";

export default function NewJobPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [scraping, setScraping] = useState(false);
  const [scrapeNote, setScrapeNote] = useState("");
  const [prefill, setPrefill] = useState(null);
  const [error, setError] = useState("");
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [pendingPayload, setPendingPayload] = useState(null);

  const handleQuickAdd = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setScraping(true);
    setScrapeNote("");
    try {
      const result = await api.quickAddFromUrl(url.trim());
      setPrefill({
        job_title: result.job_title || "",
        company_name: result.company_name || "",
        job_url: result.job_url,
      });
      setScrapeNote(result.note);
    } catch (err) {
      setScrapeNote("Couldn't process that URL — please fill in the form manually.");
    } finally {
      setScraping(false);
    }
  };

  const submitJob = async (payload, force = false) => {
    setError("");
    setSubmitting(true);
    try {
      const job = await api.createJob({ ...payload, force_create: force });
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setDuplicateWarning(err.detail?.message || "A matching application already exists.");
        setPendingPayload(payload);
      } else {
        setError(err instanceof ApiError ? err.message : "Couldn't save this application.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="new-job-page">
      <h1>Add an application</h1>
      <p className="page-subtitle">Log a new job you've applied to.</p>

      <div className="quick-add-box">
        <form onSubmit={handleQuickAdd} className="quick-add-form">
          <input
            type="url"
            placeholder="Paste a job posting URL to prefill title & company"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button className="btn btn-secondary btn-sm" type="submit" disabled={scraping}>
            {scraping ? "Fetching..." : "Prefill from URL"}
          </button>
        </form>
        {scrapeNote && <p className="quick-add-note">{scrapeNote}</p>}
      </div>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {duplicateWarning && (
        <div className="banner-info" role="alert">
          <p style={{ marginBottom: 8 }}>{duplicateWarning}</p>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => submitJob(pendingPayload, true)}
            disabled={submitting}
          >
            Add it anyway
          </button>
        </div>
      )}

      <JobForm
        key={prefill ? "prefilled" : "blank"}
        initialForm={{ ...buildInitialForm(null), ...prefill }}
        onSubmit={(payload) => submitJob(payload, false)}
        submitLabel="Add application"
        submitting={submitting}
      />
    </div>
  );
}
