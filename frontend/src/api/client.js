const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function getToken() {
  return localStorage.getItem("m4_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("m4_token", token);
  } else {
    localStorage.removeItem("m4_token");
  }
}

/**
 * Core request helper. Attaches the JWT if present, parses JSON responses,
 * and throws a typed ApiError with a human-readable message on failure so
 * every caller gets consistent error handling without repeating try/catch
 * boilerplate for status codes.
 */
async function request(path, { method = "GET", body, isForm = false, headers = {} } = {}) {
  const token = getToken();
  const finalHeaders = { ...headers };
  if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  if (body && !isForm) finalHeaders["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: isForm ? body : body ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      "Could not reach the server. Check your connection and that the API is running.",
      0,
      null
    );
  }

  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const data = isJson ? await response.json().catch(() => null) : await response.text();

  if (!response.ok) {
    const detail = isJson ? data?.detail : data;
    const message =
      typeof detail === "string" && detail.trim()
        ? detail
        : detail?.message || humanizeStatus(response.status);
    throw new ApiError(message, response.status, detail);
  }

  return data;
}

function humanizeStatus(status) {
  switch (status) {
    case 401:
      return "Your session has expired. Please log in again.";
    case 403:
      return "You don't have permission to do that.";
    case 404:
      return "That item couldn't be found.";
    case 409:
      return "That already exists.";
    case 413:
      return "That file is too large.";
    case 422:
      return "Some of the information provided isn't valid.";
    default:
      return "Something went wrong. Please try again.";
  }
}

export const api = {
  register: (email, password) =>
    request("/auth/register", { method: "POST", body: { email, password } }),

  login: async (email, password) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const data = await request("/auth/login", {
      method: "POST",
      body: form,
      isForm: true,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  },

  me: () => request("/auth/me"),

  listJobs: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.set(k, v);
    });
    const qs = query.toString();
    return request(`/jobs${qs ? `?${qs}` : ""}`);
  },

  getJob: (id) => request(`/jobs/${id}`),

  createJob: (payload) => request("/jobs", { method: "POST", body: payload }),

  updateJob: (id, payload) => request(`/jobs/${id}`, { method: "PATCH", body: payload }),

  updateStatus: (id, status) =>
    request(`/jobs/${id}/status`, { method: "PATCH", body: { status } }),

  archiveJob: (id, archived) =>
    request(`/jobs/${id}/archive?archived=${archived}`, { method: "PATCH" }),

  deleteJob: (id) => request(`/jobs/${id}`, { method: "DELETE" }),

  checkDuplicate: (companyName, jobTitle) =>
    request(
      `/jobs/check-duplicate?company_name=${encodeURIComponent(
        companyName
      )}&job_title=${encodeURIComponent(jobTitle)}`
    ),

  quickAddFromUrl: (url) =>
    request("/jobs/quick-add-from-url", { method: "POST", body: { url } }),

  listTags: () => request("/tags"),

  deleteTag: (id) => request(`/tags/${id}`, { method: "DELETE" }),

  getAnalytics: () => request("/analytics"),

  uploadAttachment: (jobId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/jobs/${jobId}/attachments`, { method: "POST", body: form, isForm: true });
  },

  deleteAttachment: (id) => request(`/attachments/${id}`, { method: "DELETE" }),

  downloadAttachment: async (id, filename) => {
    const token = getToken();
    const response = await fetch(`${API_URL}/attachments/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new ApiError("Could not download that file.", response.status, null);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "attachment";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * The backend's CSV endpoint expects a Bearer header, which a plain <a href>
   * download link can't send. So we fetch it authenticated, then hand the
   * browser a blob URL to download - same end result, works with our auth model.
   */
  downloadCsv: async () => {
    const token = getToken();
    const response = await fetch(`${API_URL}/export/csv`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new ApiError("Could not export your applications right now.", response.status, null);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "job_applications.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export { API_URL };
