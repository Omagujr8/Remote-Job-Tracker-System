import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/", label: "Board", end: true },
  { to: "/list", label: "All applications" },
  { to: "/analytics", label: "Analytics" },
];

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <div className="shell-brand">
          <span className="shell-brand-mark" aria-hidden="true">
            &#9670;
          </span>
          <span className="shell-brand-name">M4 Job Tracker</span>
        </div>

        <nav className="shell-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => "shell-nav-link" + (isActive ? " is-active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="shell-footer">
          <div className="shell-user" title={user?.email}>
            {user?.email}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={logout}>
            Log out
          </button>
        </div>
      </aside>

      <main className="shell-main">
        <Outlet />
      </main>
    </div>
  );
}
