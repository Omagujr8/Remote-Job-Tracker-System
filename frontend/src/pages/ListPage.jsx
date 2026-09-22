import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { STATUS_ORDER, STATUS_META } from "../statusMeta";
import { api, ApiError } from "../api/client";
import "./ListPage.css";

export default function ListPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [exporting, setExporting] = useState(false);

  const loadJobs = useCallback(async () => {
    setError("");
    try {
      const data = await api.listJobs({
        search: search || undefined,
        status_filter: statusFilter || undefined,
        include_archived: includeArchived,
      });
      setJobs(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your applications.");
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, includeArchived]);

  useEffect(() => {
    const timeout = setTimeout(loadJobs, 250); // debounce search typing
    return () => clearTimeout(timeout);
  }, [loadJobs]);

  const handleExport = async () => {
    setExporting(true);
    setError("");
    try {
      await api.downloadCsv();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't export your applications.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="list-page">
      <div className="list-header">
        <div>
          <h1>All applications</h1>
          <p className="page-subtitle">Search, filter, and export your full history.</p>
        </div>
        <div className="list-header-actions">
          <button className="btn btn-secondary" onClick={handleExport} disabled={exporting}>
            {exporting ? "Exporting..." : "Export CSV"}
          </button>
          <Link to="/jobs/new" className="btn btn-primary">
            Add application
          </Link>
        </div>
      </div>

      <div className="list-filters">
        <input
          type="search"
          placeholder="Search title, company, or notes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="list-search"
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          {STATUS_ORDER.map((s) => (
            <option key={s} value={s}>
              {STATUS_META[s].label}
            </option>
          ))}
        </select>
        <label className="list-archive-toggle">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
          />
          Show archived
        </label>
      </div>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <p className="page-subtitle">Loading...</p>
      ) : jobs.length === 0 ? (
        <EmptyState
          title="No applications match"
          message="Try clearing your filters, or log a new application."
          actionLabel="Add application"
          onAction={() => (window.location.href = "/jobs/new")}
        />
      ) : (
        <table className="job-table">
          <thead>
            <tr>
              <th>Job title</th>
              <th>Company</th>
              <th>Status</th>
              <th>Applied</th>
              <th>Location</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className={job.is_archived ? "is-archived-row" : ""}>
                <td>
                  <Link to={`/jobs/${job.id}`} className="job-table-title">
                    {job.job_title}
                  </Link>
                </td>
                <td>{job.company_name}</td>
                <td>
                  <StatusBadge status={job.status} />
                </td>
                <td>{job.application_date}</td>
                <td>{job.location || "—"}</td>
                <td>{job.is_archived && <span className="archived-tag">Archived</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
