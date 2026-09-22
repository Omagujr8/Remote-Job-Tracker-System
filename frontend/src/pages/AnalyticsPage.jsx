import { useEffect, useState } from "react";
import { STATUS_META } from "../statusMeta";
import { api, ApiError } from "../api/client";
import "./AnalyticsPage.css";

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getAnalytics()
      .then(setData)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Couldn't load analytics.")
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="page-subtitle">Loading...</p>;
  if (error) return <div className="banner-error">{error}</div>;
  if (!data || data.total_applications === 0) {
    return (
      <div>
        <h1>Analytics</h1>
        <p className="page-subtitle">Log a few applications to see your stats here.</p>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <h1>Analytics</h1>
      <p className="page-subtitle">A read on how your search is trending.</p>

      <div className="analytics-stats">
        <StatCard label="Active applications" value={data.active_applications} />
        <StatCard label="Interview rate" value={`${data.interview_rate}%`} />
        <StatCard label="Offer rate" value={`${data.offer_rate}%`} />
        <StatCard label="Going stale" value={data.stale_applications} accent={data.stale_applications > 0} />
      </div>

      <div className="analytics-secondary">
        <StatCard label="Last 7 days" value={data.applications_last_7_days} small />
        <StatCard label="Last 30 days" value={data.applications_last_30_days} small />
        <StatCard label="Total logged" value={data.total_applications} small />
      </div>

      <h2 className="analytics-breakdown-title">Status breakdown</h2>
      <div className="analytics-breakdown">
        {data.status_breakdown.map((row) => {
          const meta = STATUS_META[row.status] || {};
          const pct = Math.round((row.count / data.total_applications) * 100);
          return (
            <div className="breakdown-row" key={row.status}>
              <span className="breakdown-label">{meta.label || row.status}</span>
              <div className="breakdown-bar-track">
                <div
                  className="breakdown-bar-fill"
                  style={{ width: `${pct}%`, background: meta.color }}
                />
              </div>
              <span className="breakdown-count">{row.count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatCard({ label, value, small, accent }) {
  return (
    <div className={"stat-card" + (small ? " stat-card-small" : "") + (accent ? " stat-card-accent" : "")}>
      <p className="stat-card-value">{value}</p>
      <p className="stat-card-label">{label}</p>
    </div>
  );
}
