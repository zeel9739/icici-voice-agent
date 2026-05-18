import { useEffect, useState } from "react";
import type { DialResponse, Lead, LeadListResponse } from "../types";
import { API_BASE } from "../lib/api";
import { LeadStatusBadge } from "./LeadStatusBadge";
import styles from "./LeadDashboard.module.css";

interface Props {
  onDial: (session: DialResponse) => void;
}

export function LeadDashboard({ onDial }: Props) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dialingId, setDialingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── New lead form ──────────────────────────────────────────────────────────
  const [form, setForm] = useState({ name: "", phone_number: "" });

  async function fetchLeads() {
    const res = await fetch(`${API_BASE}/api/v1/leads?page_size=50`);
    const data: LeadListResponse = await res.json();
    setLeads(data.items);
    setTotal(data.total);
    setLoading(false);
  }

  useEffect(() => { fetchLeads(); }, []);

  async function handleCreateLead(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await fetch(`${API_BASE}/api/v1/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, fund_preference: "unknown" }),
    });
    if (!res.ok) {
      const err = await res.json();
      setError(err.detail ?? "Failed to create lead");
      return;
    }
    setForm({ name: "", phone_number: "" });
    fetchLeads();
  }

  async function handleDial(leadId: string) {
    setError(null);

    // Request mic permission before connecting — required for WebRTC audio
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop()); // release immediately; LiveKit will re-acquire
    } catch {
      setError("Microphone access is required to start the call. Please allow mic permission and try again.");
      return;
    }

    setDialingId(leadId);
    const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/dial`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json();
      setError(err.detail ?? "Failed to start call");
      setDialingId(null);
      return;
    }
    const data: DialResponse = await res.json();
    onDial(data);
    setDialingId(null);
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>🏦</span>
          <div>
            <h1>ICICI Prudential AMC</h1>
            <p>Lead Qualification Bot</p>
          </div>
        </div>
        <span className={styles.totalBadge}>{total} leads</span>
      </header>

      <main className={styles.main}>
        {/* ── Add Lead Form ──────────────────────────────────────────────── */}
        <section className={styles.card}>
          <h2>Add New Lead</h2>
          {error && <p className={styles.error}>{error}</p>}
          <form onSubmit={handleCreateLead} className={styles.form}>
            <input
              required
              placeholder="Full name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              required
              placeholder="Phone (+91XXXXXXXXXX)"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
            />
            <button type="submit" className={styles.btnPrimary}>Add Lead</button>
          </form>
        </section>

        {/* ── Lead Table ─────────────────────────────────────────────────── */}
        <section className={styles.card}>
          <h2>Leads</h2>
          {loading ? (
            <p className={styles.muted}>Loading…</p>
          ) : leads.length === 0 ? (
            <p className={styles.muted}>No leads yet. Add one above.</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Fund</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id}>
                    <td>{lead.name}</td>
                    <td>{lead.phone_number}</td>
                    <td><LeadStatusBadge status={lead.status} /></td>
                    <td>{lead.fund_preference}</td>
                    <td>
                      <button
                        className={styles.btnCall}
                        disabled={dialingId === lead.id}
                        onClick={() => handleDial(lead.id)}
                      >
                        {dialingId === lead.id ? "Connecting…" : "📞 Call"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}
