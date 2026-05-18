import type { LeadStatus } from "../types";

const COLOURS: Record<LeadStatus, string> = {
  pending: "#64748b",
  interested: "#16a34a",
  not_interested: "#dc2626",
  callback_requested: "#d97706",
  unreachable: "#9333ea",
};

const LABELS: Record<LeadStatus, string> = {
  pending: "Pending",
  interested: "Interested",
  not_interested: "Not Interested",
  callback_requested: "Call Back",
  unreachable: "Unreachable",
};

interface Props {
  status: LeadStatus;
}

export function LeadStatusBadge({ status }: Props) {
  return (
    <span
      style={{
        display: "inline-block",
        background: COLOURS[status] + "20",
        color: COLOURS[status],
        border: `1px solid ${COLOURS[status]}40`,
        borderRadius: 999,
        padding: "2px 10px",
        fontSize: "0.78rem",
        fontWeight: 600,
      }}
    >
      {LABELS[status]}
    </span>
  );
}
