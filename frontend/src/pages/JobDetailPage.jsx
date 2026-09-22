import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import JobForm, { buildInitialForm } from "../components/JobForm";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import { STATUS_ORDER, STATUS_META } from "../statusMeta";
import { api, ApiError } from "../api/client";
import "./JobDetailPage.css";

export default function JobDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const loadJob = useCallback(async () => {
    setError("");
    try {
      const data = await api.getJob(id);
      setJob(data);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? "This application couldn't be found."
          : "Couldn't load this application."
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  const handleSave = async (payload) => {
    setSaving(true);
    setError("");
    try {
      const updated = await api.updateJob(id, payload);
      setJob(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save your changes.");
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value;
    const previous = job;
    setJob((j) => ({ ...j, status: newStatus }));
    try {
      const updated = await api.updateStatus(id, newStatus);
      setJob(updated);
    } catch (err) {
      setJob(previous);
      setError(err instanceof ApiError ? err.message : "Couldn't update the status.");
    }
  };

  const handleArchiveToggle = async () => {
    try {
      const updated = await api.archiveJob(id, !job.is_archived);
      setJob(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update the archive state.");
    }
  };

  const handleDelete = async () => {
    try {
      await api.deleteJob(id);
      navigate("/list");
    } catch (err) {
      setConfirmDelete(false);
      setError(err instanceof ApiError ? err.message : "Couldn't delete this application.");
    }
  };

  const handleFileSelected = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError("");
    try {
      await api.uploadAttachment(id, file);
      await loadJob();
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Couldn't upload that file.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    try {
      await api.deleteAttachment(attachmentId);
      await loadJob();
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Couldn't delete that file.");
    }
  };

  if (loading) return <p className="page-subtitle">Loading...</p>;

  if (!job) {
    return (
      <div>
        <div className="banner-error" role="alert">
          {error || "This application couldn't be found."}
        </div>
        <Link to="/list" className="btn btn-secondary">
          Back to all applications
        </Link>
      </div>
    );
  }

  return (
    <div className="job-detail-page">
      <Link to="/list" className="job-detail-back">
        &larr; All applications
      </Link>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {editing ? (
        <>
          <h1>Edit application</h1>
          <JobForm
            initialForm={buildInitialForm(job)}
            initialTags={job.tags.map((t) => t.name)}
            onSubmit={handleSave}
            submitLabel="Save changes"
            submitting={saving}
          />
          <button className="btn btn-ghost" onClick={() => setEditing(false)} style={{ marginTop: 8 }}>
            Cancel
          </button>
        </>
      ) : (
        <>
          <div className="job-detail-header">
            <div>
              <p className="job-detail-company">{job.company_name}</p>
              <h1>{job.job_title}</h1>
            </div>
            <div className="job-detail-actions">
              <button className="btn btn-secondary" onClick={() => setEditing(true)}>
                Edit
              </button>
              <button className="btn btn-secondary" onClick={handleArchiveToggle}>
                {job.is_archived ? "Unarchive" : "Archive"}
              </button>
              <button className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
                Delete
              </button>
            </div>
          </div>

          <div className="job-detail-status-row">
            <StatusBadge status={job.status} />
            {job.is_stale && (
              <span className="job-detail-stale">
                No updates in {job.days_since_update} days — consider following up
              </span>
            )}
            {job.is_archived && <span className="archived-tag">Archived</span>}
          </div>

          <div className="field job-detail-status-select">
            <label htmlFor="status-select">Move to stage</label>
            <select id="status-select" value={job.status} onChange={handleStatusChange}>
              {STATUS_ORDER.map((s) => (
                <option key={s} value={s}>
                  {STATUS_META[s].label}
                </option>
              ))}
            </select>
          </div>

          <dl className="job-detail-grid">
            <div>
              <dt>Applied</dt>
              <dd>{job.application_date}</dd>
            </div>
            <div>
              <dt>Salary range</dt>
              <dd>{job.salary_range || "—"}</dd>
            </div>
            <div>
              <dt>Location</dt>
              <dd>{job.location || "—"}</dd>
            </div>
            <div>
              <dt>Contact</dt>
              <dd>{job.contact_info || "—"}</dd>
            </div>
            <div>
              <dt>Referred by</dt>
              <dd>{job.referred_by || "—"}</dd>
            </div>
            <div>
              <dt>Posting</dt>
              <dd>
                {job.job_url ? (
                  <a href={job.job_url} target="_blank" rel="noreferrer">
                    View posting &#8599;
                  </a>
                ) : (
                  "—"
                )}
              </dd>
            </div>
          </dl>

          {job.tags.length > 0 && (
            <div className="job-detail-tags">
              {job.tags.map((t) => (
                <span key={t.id} className="job-card-tag">
                  {t.name}
                </span>
              ))}
            </div>
          )}

          <div className="job-detail-section">
            <h2>Notes</h2>
            <p className="job-detail-notes">{job.interview_notes || "No notes yet."}</p>
          </div>

          <div className="job-detail-section">
            <div className="job-detail-section-header">
              <h2>Attachments</h2>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                {uploading ? "Uploading..." : "Upload file"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                className="visually-hidden"
                onChange={handleFileSelected}
              />
            </div>
            {uploadError && (
              <div className="banner-error" role="alert">
                {uploadError}
              </div>
            )}
            {job.attachments.length === 0 ? (
              <p className="job-detail-empty">No files attached yet — add a resume or cover letter.</p>
            ) : (
              <ul className="attachment-list">
                {job.attachments.map((att) => (
                  <li key={att.id}>
                    <button
                      className="attachment-link"
                      onClick={() => api.downloadAttachment(att.id, att.filename)}
                    >
                      {att.filename}
                    </button>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleDeleteAttachment(att.id)}
                      aria-label={`Delete ${att.filename}`}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this application?"
        message={`This permanently removes "${job.job_title}" at ${job.company_name}, including its notes and attachments. This can't be undone.`}
        confirmLabel="Delete"
        danger
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
