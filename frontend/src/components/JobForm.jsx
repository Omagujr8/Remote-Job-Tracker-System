import { useState } from "react";
import TagInput from "./TagInput";
import { STATUS_ORDER, STATUS_META } from "../statusMeta";
import "./JobForm.css";

const EMPTY_FORM = {
  job_title: "",
  company_name: "",
  status: "applied",
  application_date: new Date().toISOString().slice(0, 10),
  salary_range: "",
  location: "",
  contact_info: "",
  interview_notes: "",
  job_url: "",
  referred_by: "",
};

export function buildInitialForm(job) {
  if (!job) return { ...EMPTY_FORM };
  return {
    job_title: job.job_title || "",
    company_name: job.company_name || "",
    status: job.status || "applied",
    application_date: job.application_date || EMPTY_FORM.application_date,
    salary_range: job.salary_range || "",
    location: job.location || "",
    contact_info: job.contact_info || "",
    interview_notes: job.interview_notes || "",
    job_url: job.job_url || "",
    referred_by: job.referred_by || "",
  };
}

export default function JobForm({
  initialForm,
  initialTags = [],
  onSubmit,
  submitLabel = "Save",
  submitting,
  fieldErrors = {},
}) {
  const [form, setForm] = useState(initialForm || EMPTY_FORM);
  const [tags, setTags] = useState(initialTags);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ ...form, tag_names: tags });
  };

  return (
    <form onSubmit={handleSubmit} className="job-form">
      <div className="job-form-row">
        <div className="field">
          <label htmlFor="job_title">Job title *</label>
          <input
            id="job_title"
            required
            value={form.job_title}
            onChange={update("job_title")}
            maxLength={255}
          />
          {fieldErrors.job_title && <span className="field-error">{fieldErrors.job_title}</span>}
        </div>
        <div className="field">
          <label htmlFor="company_name">Company *</label>
          <input
            id="company_name"
            required
            value={form.company_name}
            onChange={update("company_name")}
            maxLength={255}
          />
          {fieldErrors.company_name && <span className="field-error">{fieldErrors.company_name}</span>}
        </div>
      </div>

      <div className="job-form-row">
        <div className="field">
          <label htmlFor="status">Status</label>
          <select id="status" value={form.status} onChange={update("status")}>
            {STATUS_ORDER.map((s) => (
              <option key={s} value={s}>
                {STATUS_META[s].label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="application_date">Application date *</label>
          <input
            id="application_date"
            type="date"
            required
            value={form.application_date}
            onChange={update("application_date")}
          />
        </div>
      </div>

      <div className="job-form-row">
        <div className="field">
          <label htmlFor="salary_range">Salary range</label>
          <input
            id="salary_range"
            value={form.salary_range}
            onChange={update("salary_range")}
            placeholder="e.g. $110k–130k"
            maxLength={120}
          />
        </div>
        <div className="field">
          <label htmlFor="location">Location</label>
          <input
            id="location"
            value={form.location}
            onChange={update("location")}
            placeholder="e.g. Remote (US)"
            maxLength={255}
          />
        </div>
      </div>

      <div className="job-form-row">
        <div className="field">
          <label htmlFor="job_url">Job posting URL</label>
          <input
            id="job_url"
            type="url"
            value={form.job_url}
            onChange={update("job_url")}
            placeholder="https://..."
            maxLength={1000}
          />
        </div>
        <div className="field">
          <label htmlFor="referred_by">Referred by</label>
          <input
            id="referred_by"
            value={form.referred_by}
            onChange={update("referred_by")}
            placeholder="e.g. Jordan on the platform team"
            maxLength={255}
          />
        </div>
      </div>

      <div className="field">
        <label htmlFor="contact_info">Contact info</label>
        <input
          id="contact_info"
          value={form.contact_info}
          onChange={update("contact_info")}
          placeholder="Recruiter name, email or phone"
          maxLength={500}
        />
      </div>

      <div className="field">
        <label htmlFor="interview_notes">Notes</label>
        <textarea
          id="interview_notes"
          rows={5}
          value={form.interview_notes}
          onChange={update("interview_notes")}
          placeholder="Interview impressions, questions asked, follow-ups to send..."
        />
      </div>

      <div className="field">
        <label htmlFor="tags">Tags</label>
        <TagInput tags={tags} onChange={setTags} />
      </div>

      <button className="btn btn-primary" type="submit" disabled={submitting}>
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
