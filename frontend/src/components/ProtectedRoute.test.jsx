import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { AuthProvider } from "../context/AuthContext";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function renderProtected(initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route
            path="/board"
            element={
              <ProtectedRoute>
                <div>Secret board</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("redirects to /login when there is no session", async () => {
    renderProtected(["/board"]);
    await waitFor(() => expect(screen.getByText("Login page")).toBeInTheDocument());
    expect(screen.queryByText("Secret board")).not.toBeInTheDocument();
  });

  it("renders the protected content when a valid session exists", async () => {
    localStorage.setItem("m4_token", "valid-token");
    global.fetch.mockResolvedValueOnce(jsonResponse({ id: 1, email: "a@b.com" }));

    renderProtected(["/board"]);

    await waitFor(() => expect(screen.getByText("Secret board")).toBeInTheDocument());
  });
});
