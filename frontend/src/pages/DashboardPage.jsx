import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import KanbanBoard from "../components/KanbanBoard";
import EmptyState from "../components/EmptyState";
import { api, ApiError } from "../api/client";
import "./DashboardPage.css";

export default function DashboardPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadJobs = useCallback(async () => {
    setError("");
    try {
      const data = await api.listJobs();
      setJobs(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your applications.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handleStatusChange = async (jobId, newStatus) => {
    const previous = jobs;
    setJobs((current) => current.map((j) => (j.id === jobId ? { ...j, status: newStatus } : j)));
    try {
      await api.updateStatus(jobId, newStatus);
    } catch (err) {
      setJobs(previous); // roll back on failure
      setError(
        err instanceof ApiError ? err.message : "Couldn't update the status. Please try again."
      );
    }
  };

  const staleCount = jobs.filter((j) => j.is_stale).length;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1>Board</h1>
          <p className="page-subtitle">
            {jobs.length} active application{jobs.length === 1 ? "" : "s"}
            {staleCount > 0 && (
              <span className="dashboard-stale-note"> &middot; {staleCount} going stale</span>
            )}
          </p>
        </div>
        <Link to="/jobs/new" className="btn btn-primary">
          Add application
        </Link>
      </div>

      {error && (
        <div className="banner-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <p className="page-subtitle">Loading your board...</p>
      ) : jobs.length === 0 ? (
        <EmptyState
          title="Your board is empty"
          message="Log your first application to start tracking your search."
          actionLabel="Add application"
          onAction={() => (window.location.href = "/jobs/new")}
        />
      ) : (
        <KanbanBoard jobs={jobs} onStatusChange={handleStatusChange} />
      )}
    </div>
  );
}
