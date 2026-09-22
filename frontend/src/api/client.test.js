import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, setToken, ApiError } from "../api/client";

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("attaches the Authorization header when a token is stored", async () => {
    setToken("test-token-123");
    global.fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 1, email: "a@b.com" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      })
    );

    await api.me();

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers["Authorization"]).toBe("Bearer test-token-123");
  });

  it("does not attach an Authorization header when logged out", async () => {
    global.fetch.mockResolvedValueOnce(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "content-type": "application/json" },
      })
    );

    await api.listJobs();

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers["Authorization"]).toBeUndefined();
  });

  it("throws an ApiError with the server's detail message on failure", async () => {
    global.fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Incorrect email or password" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      })
    );

    try {
      await api.login("a@b.com", "wrong");
      throw new Error("expected api.login to reject");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.message).toBe("Incorrect email or password");
      expect(err.status).toBe(401);
    }
  });

  it("falls back to a human-readable message when the server gives no detail", async () => {
    global.fetch.mockResolvedValue(
      new Response(null, { status: 500 })
    );

    await expect(api.getJob(1)).rejects.toThrow(/went wrong/i);
  });

  it("surfaces a friendly error when the network request itself fails", async () => {
    global.fetch.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    await expect(api.getJob(1)).rejects.toThrow(/could not reach the server/i);
  });

  it("builds duplicate-check query params correctly", async () => {
    global.fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ duplicate_found: false }), {
        status: 200,
        headers: { "content-type": "application/json" },
      })
    );

    await api.checkDuplicate("Acme & Co", "Backend Engineer");
    const [url] = global.fetch.mock.calls[0];
    expect(url).toContain("company_name=Acme%20%26%20Co");
    expect(url).toContain("job_title=Backend%20Engineer");
  });
});
