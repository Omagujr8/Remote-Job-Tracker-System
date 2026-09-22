export const STATUS_ORDER = [
  "applied",
  "phone_screen",
  "technical_interview",
  "onsite_interview",
  "final_interview",
  "offer",
  "rejected",
  "withdrawn",
];

export const STATUS_META = {
  applied: { label: "Applied", color: "var(--status-applied)", tint: "var(--status-applied-tint)" },
  phone_screen: {
    label: "Phone Screen",
    color: "var(--status-interviewing)",
    tint: "var(--status-interviewing-tint)",
  },
  technical_interview: {
    label: "Technical",
    color: "var(--status-interviewing)",
    tint: "var(--status-interviewing-tint)",
  },
  onsite_interview: {
    label: "Onsite",
    color: "var(--status-interviewing)",
    tint: "var(--status-interviewing-tint)",
  },
  final_interview: {
    label: "Final Round",
    color: "var(--status-interviewing)",
    tint: "var(--status-interviewing-tint)",
  },
  offer: { label: "Offer", color: "var(--status-offer)", tint: "var(--status-offer-tint)" },
  rejected: { label: "Rejected", color: "var(--status-rejected)", tint: "var(--status-rejected-tint)" },
  withdrawn: {
    label: "Withdrawn",
    color: "var(--status-withdrawn)",
    tint: "var(--status-withdrawn-tint)",
  },
};

// Kanban columns group the four interview sub-stages under one "Interviewing"
// column (with a sub-label) to keep the board scannable, while /list and
// analytics still track the finer-grained stage.
export const KANBAN_COLUMNS = [
  { key: "applied", label: "Applied", statuses: ["applied"] },
  {
    key: "interviewing",
    label: "Interviewing",
    statuses: ["phone_screen", "technical_interview", "onsite_interview", "final_interview"],
  },
  { key: "offer", label: "Offer", statuses: ["offer"] },
  { key: "closed", label: "Closed", statuses: ["rejected", "withdrawn"] },
];
