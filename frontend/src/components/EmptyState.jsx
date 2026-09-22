import "./EmptyState.css";

export default function EmptyState({ title, message, actionLabel, onAction }) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <p>{message}</p>
      {actionLabel && onAction && (
        <button className="btn btn-primary" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
