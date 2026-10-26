import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import NewJobPage from "./NewJobPage";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    quickAddFromUrl: vi.fn(),
    createJob: vi.fn(),
  },
  ApiError: class ApiError extends Error {},
}));

describe("NewJobPage URL prefill", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("updates the form when prefill is requested for another URL", async () => {
    api.quickAddFromUrl
      .mockResolvedValueOnce({
        job_title: "First role",
        company_name: "First company",
        job_url: "https://jobs.example.com/first",
        note: "Parsed successfully.",
      })
      .mockResolvedValueOnce({
        job_title: "Junior Java Developer",
        company_name: "Workly",
        job_url: "https://jobs.example.com/second",
        note: "Parsed successfully.",
      });

    render(
      <MemoryRouter>
        <NewJobPage />
      </MemoryRouter>
    );
    const urlInput = screen.getByPlaceholderText("Paste a job posting URL to prefill title & company");
    const user = userEvent.setup();

    await user.type(urlInput, "https://jobs.example.com/first");
    await user.click(screen.getByRole("button", { name: "Prefill from URL" }));

    expect(await screen.findByLabelText("Job title *")).toHaveValue("First role");
    expect(screen.getByLabelText("Job posting URL")).toHaveValue("https://jobs.example.com/first");

    await user.clear(urlInput);
    await user.type(urlInput, "https://jobs.example.com/second");
    await user.click(screen.getByRole("button", { name: "Prefill from URL" }));

    expect(await screen.findByLabelText("Job title *")).toHaveValue("Junior Java Developer");
    expect(screen.getByLabelText("Company *")).toHaveValue("Workly");
    expect(screen.getByLabelText("Job posting URL")).toHaveValue("https://jobs.example.com/second");
  });
});
