import { STATUS_META } from "../statusMeta";
import "./StatusBadge.css";

export default function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, color: "var(--ink-faint)", tint: "var(--paper-raised)" };
  return (
    <span className="status-badge" style={{ color: meta.color, background: meta.tint }}>
      {meta.label}
    </span>
  );
}
