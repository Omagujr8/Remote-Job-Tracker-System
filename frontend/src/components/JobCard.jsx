import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import { STATUS_META } from "../statusMeta";
import "./JobCard.css";

export default function JobCard({ job, onDragStart }) {
  const meta = STATUS_META[job.status] || {};

  return (
    <Link
      to={`/jobs/${job.id}`}
      className="job-card"
      draggable
      onDragStart={(e) => onDragStart(e, job)}
      style={{ "--tab-color": meta.color }}
    >
      <div className="job-card-tab" />
      <div className="job-card-body">
        <p className="job-card-company">{job.company_name}</p>
        <h3 className="job-card-title">{job.job_title}</h3>
        <div className="job-card-meta">
          <StatusBadge status={job.status} />
          {job.is_stale && <span className="job-card-stale">Stale &middot; {job.days_since_update}d</span>}
        </div>
        {job.tags?.length > 0 && (
          <div className="job-card-tags">
            {job.tags.map((t) => (
              <span key={t.id} className="job-card-tag">
                {t.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
