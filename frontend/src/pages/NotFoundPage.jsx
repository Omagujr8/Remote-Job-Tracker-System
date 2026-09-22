import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div style={{ padding: 48, textAlign: "center" }}>
      <h1>Page not found</h1>
      <p className="page-subtitle" style={{ margin: "8px 0 24px" }}>
        That page doesn't exist.
      </p>
      <Link to="/" className="btn btn-primary">
        Back to your board
      </Link>
    </div>
  );
}
