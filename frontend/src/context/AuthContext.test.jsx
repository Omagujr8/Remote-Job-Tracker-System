import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthContext";

function Probe() {
  const { user, loading, login, register, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.email : "none"}</span>
      <button onClick={() => login("a@b.com", "password123")}>login</button>
      <button onClick={() => register("new@b.com", "password123")}>register</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts logged out with no stored token", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    // No /auth/me call should have been made without a token.
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("restores the session from a stored token on mount", async () => {
    localStorage.setItem("m4_token", "existing-token");
    global.fetch.mockResolvedValueOnce(jsonResponse({ id: 1, email: "stored@b.com" }));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("stored@b.com"));
  });

  it("clears an invalid stored token instead of leaving the app stuck", async () => {
    localStorage.setItem("m4_token", "bad-token");
    global.fetch.mockResolvedValueOnce(jsonResponse({ detail: "Could not validate credentials" }, 401));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("none"));
    expect(localStorage.getItem("m4_token")).toBeNull();
  });

  it("logs in successfully and stores the user", async () => {
    global.fetch
      .mockResolvedValueOnce(jsonResponse({ access_token: "new-token" })) // /auth/login
      .mockResolvedValueOnce(jsonResponse({ id: 2, email: "a@b.com" })); // /auth/me

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));

    await userEvent.click(screen.getByText("login"));

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("a@b.com"));
    expect(localStorage.getItem("m4_token")).toBe("new-token");
  });

  it("logout clears the user and the stored token", async () => {
    global.fetch
      .mockResolvedValueOnce(jsonResponse({ access_token: "new-token" }))
      .mockResolvedValueOnce(jsonResponse({ id: 2, email: "a@b.com" }));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));
    await userEvent.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("a@b.com"));

    await userEvent.click(screen.getByText("logout"));

    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(localStorage.getItem("m4_token")).toBeNull();
  });

  it("register calls register then logs in automatically", async () => {
    global.fetch
      .mockResolvedValueOnce(jsonResponse({ id: 3, email: "new@b.com" })) // /auth/register
      .mockResolvedValueOnce(jsonResponse({ access_token: "reg-token" })) // /auth/login
      .mockResolvedValueOnce(jsonResponse({ id: 3, email: "new@b.com" })); // /auth/me

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));

    await userEvent.click(screen.getByText("register"));

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("new@b.com"));
  });
});
