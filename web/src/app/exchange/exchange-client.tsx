"use client";

import { useMemo, useState } from "react";
import { CsvButton } from "@/components/csv-button";
import { Card, StatGrid, StatTile } from "@/components/ui";
import { API_BASE } from "@/lib/live";

// Site root for files in public/ (e.g. "/driw" on XAMPP); the API lives at <root>/api.
const SITE_BASE = API_BASE.replace(/\/api$/, "");

type ReportTypeInfo = { key: string; title: string; issuer: string; description: string; template: string };
type ProfileInfo = { id: string; name: string; report_type: string; description: string };
type Issue = { code: string; field: string | null; severity: string; message: string; action: string };
type ReportRow = { row: number; status: string; issues: Issue[]; resolved: string[] };
type Report = {
  ok: boolean;
  action: "validate" | "submit";
  file: string;
  file_errors?: string[];
  error?: string;
  report_title?: string;
  profile?: { name: string };
  summary?: Record<string, number>;
  rows?: ReportRow[];
  submitted?: { file: string | null; rows_written: number; rows_excluded: number; load?: { ok: boolean; message: string; seconds: number } };
};

const STATUS: Record<string, { label: string; className: string }> = {
  accepted: { label: "Accepted", className: "bg-[#e6f4e6] text-[#0b5d0b]" },
  corrected: { label: "Corrected", className: "bg-[#e3edfa] text-[#1c4f8f]" },
  warning: { label: "Warning", className: "bg-[#fdf1d6] text-[#6b4a00]" },
  duplicate: { label: "Duplicate", className: "bg-[#ecebe6] text-[#52514e]" },
  rejected: { label: "Rejected", className: "bg-[#fbe4e4] text-[#9b2424]" },
};

export function TemplateLink({ href }: { href: string }) {
  return (
    <a
      href={`${SITE_BASE}/${href}`}
      download
      className="mt-2 w-fit rounded-md border border-[var(--border)] px-3 py-1.5 text-sm font-medium hover:bg-[var(--grid)]"
    >
      Download template (.xlsx)
    </a>
  );
}

export function ExchangeForm({ reportTypes, profiles }: { reportTypes: ReportTypeInfo[]; profiles: ProfileInfo[] }) {
  const [type, setType] = useState(reportTypes[0].key);
  const [profile, setProfile] = useState("standard");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState<null | "validate" | "submit">(null);
  const [report, setReport] = useState<Report | null>(null);

  const layouts = useMemo(() => profiles.filter((p) => p.report_type === type), [profiles, type]);
  const chosen = layouts.find((p) => p.id === profile);

  async function send(action: "validate" | "submit") {
    if (!file) return;
    setBusy(action);
    setReport(null);
    const form = new FormData();
    form.append("action", action);
    form.append("type", type);
    form.append("profile", profile);
    form.append("file", file);
    try {
      const response = await fetch(`${API_BASE}/intake.php`, { method: "POST", body: form });
      const body = await response.json();
      setReport(body.error ? { ok: false, action, file: file.name, file_errors: [body.error] } : body);
    } catch {
      setReport({ ok: false, action, file: file.name, file_errors: ["The DRIW server could not be reached."] });
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card title="2. Check and submit a report" subtitle="Every row is checked with the warehouse's own data-quality rules before anything is stored">
      {!API_BASE && (
        <p className="mb-4 rounded-md bg-[var(--notice-bg)] px-3 py-2 text-sm text-[var(--notice-ink)]">
          Checking and submitting need the DRIW server (the XAMPP installation at http://localhost/driw/). This copy of
          the site is static, so the form is disabled here.
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-2">Report type</span>
          <select
            value={type}
            onChange={(e) => {
              setType(e.target.value);
              setProfile("standard");
              setReport(null);
            }}
            className="rounded-md border border-[var(--border)] bg-surface px-3 py-1.5"
          >
            {reportTypes.map((t) => (
              <option key={t.key} value={t.key}>
                {t.title}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-2">Layout of the file</span>
          <select
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
            className="rounded-md border border-[var(--border)] bg-surface px-3 py-1.5"
          >
            <option value="standard">DRIW template</option>
            {layouts.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-2">File (.xlsx or .csv, up to 10 MB)</span>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setReport(null);
            }}
            className="text-sm file:mr-3 file:rounded-md file:border file:border-[var(--border)] file:bg-surface file:px-3 file:py-1.5"
          />
        </label>
      </div>
      {chosen && <p className="mt-2 text-sm text-ink-2">{chosen.description}</p>}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={!API_BASE || !file || busy !== null}
          onClick={() => send("validate")}
          className="rounded-md border border-[var(--border)] px-4 py-2 text-sm font-medium hover:bg-[var(--grid)] disabled:opacity-50"
        >
          Check file
        </button>
        <button
          type="button"
          disabled={!API_BASE || !file || busy !== null}
          onClick={() => send("submit")}
          className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Check and submit
        </button>
        {busy && (
          <p className="text-sm text-ink-2" role="status">
            {busy === "validate"
              ? "Checking every row against the warehouse rules…"
              : "Checking, then loading into the warehouse and re-running its checks (about half a minute)…"}
          </p>
        )}
      </div>

      {report && <ValidationReport report={report} />}
    </Card>
  );
}

function ValidationReport({ report }: { report: Report }) {
  if (!report.ok) {
    return (
      <div className="mt-5 rounded-md border border-[#e9b4b4] bg-[#fbe4e4] px-4 py-3 text-sm text-[#7a1c1c]" role="alert">
        <p className="font-medium">The file could not be checked</p>
        <ul className="mt-1 list-disc pl-5">
          {(report.file_errors ?? []).map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      </div>
    );
  }
  const s = report.summary ?? {};
  const rows = report.rows ?? [];
  return (
    <div className="mt-5">
      <p className="text-sm text-ink-2">
        <span className="font-medium text-ink">{report.file}</span> · {report.report_title} · layout: {report.profile?.name}
      </p>
      <div className="mt-3">
        <StatGrid>
          <StatTile label="Rows" value={String(s.rows ?? 0)} />
          <StatTile label="Accepted" value={String(s.accepted ?? 0)} detail="as written" />
          <StatTile label="Corrected" value={String(s.corrected ?? 0)} detail="matched or converted" />
          <StatTile label="Warnings" value={String(s.warning ?? 0)} detail="kept and flagged" />
          <StatTile label="Rejected" value={String(s.rejected ?? 0)} detail="see reasons below" />
          <StatTile label="Duplicates" value={String(s.duplicate ?? 0)} detail="ignored" />
        </StatGrid>
      </div>

      {report.submitted && (
        <div
          className={`mt-4 rounded-md px-4 py-3 text-sm ${
            report.submitted.load && !report.submitted.load.ok ? "bg-[#fbe4e4] text-[#7a1c1c]" : "bg-[#e6f4e6] text-[#0b5d0b]"
          }`}
          role="status"
        >
          <p className="font-medium">
            Submitted: {report.submitted.rows_written} row(s) stored
            {report.submitted.rows_excluded > 0 && `, ${report.submitted.rows_excluded} not stored (submission rules)`}.
          </p>
          {report.submitted.load && <p>{report.submitted.load.message}</p>}
          <p className="mt-1">
            Rows rejected by the data-quality rules are kept in the warehouse&apos;s quarantine with their reasons;
            correct them and submit the file again to replace this version.
          </p>
        </div>
      )}

      <div className="mt-4 flex justify-end">
        <CsvButton
          filename={`driw-check-${report.file.replace(/\.[^.]+$/, "")}`}
          columns={[
            { key: "row", label: "Row" },
            { key: "status", label: "Status" },
            { key: "issues", label: "Issues" },
            { key: "resolved", label: "Resolved as" },
          ]}
          rows={rows.map((r) => ({
            row: r.row,
            status: STATUS[r.status]?.label ?? r.status,
            issues: r.issues.map((i) => `${i.code}${i.field ? ` (${i.field})` : ""}: ${i.message}`).join(" | "),
            resolved: r.resolved.join(" | "),
          }))}
        />
      </div>
      <div className="mt-2 max-h-[32rem] overflow-auto rounded-md border border-[var(--border)]">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-surface text-ink-2">
            <tr>
              <th scope="col" className="border-b border-[var(--border)] px-3 py-2 font-medium">Row</th>
              <th scope="col" className="border-b border-[var(--border)] px-3 py-2 font-medium">Status</th>
              <th scope="col" className="border-b border-[var(--border)] px-3 py-2 font-medium">What DRIW found</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.row} className="border-b border-[var(--border)] align-top last:border-0">
                <td className="tabular px-3 py-2">{r.row}</td>
                <td className="px-3 py-2">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${STATUS[r.status]?.className ?? ""}`}>
                    {STATUS[r.status]?.label ?? r.status}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <ul className="flex flex-col gap-1">
                    {r.issues
                      .filter((i) => i.severity !== "info" || r.status === "rejected")
                      .map((i, k) => (
                        <li key={`i${k}`}>
                          <span className="font-medium">{i.severity === "reject" ? "Rejected" : "Flagged"}:</span>{" "}
                          {i.message}
                          {i.field && <span className="text-ink-2"> ({i.field})</span>}
                        </li>
                      ))}
                    {r.resolved.map((x, k) => (
                      <li key={`r${k}`} className="text-ink-2">
                        {x}
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ExcelExport({ options }: { options: { code: string; label: string }[] }) {
  const [event, setEvent] = useState("ALL");
  const href = `${API_BASE}/export.php${event === "ALL" ? "" : `?event=${event}`}`;
  if (!API_BASE) {
    return (
      <p className="text-sm text-ink-2">
        The live Excel export needs the DRIW server (http://localhost/driw/). Every table on the dashboards also has a
        Download CSV button that works anywhere.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-ink-2">Scope</span>
        <select
          value={event}
          onChange={(e) => setEvent(e.target.value)}
          className="rounded-md border border-[var(--border)] bg-surface px-3 py-1.5"
        >
          <option value="ALL">All events, 2020–2025</option>
          {options.map((o) => (
            <option key={o.code} value={o.code}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <a href={href} className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white">
        Download Excel workbook
      </a>
      <p className="w-full text-xs text-muted">
        Sheets: Event summary, Impact cube, Province impact, Evacuation daily, Response performance, Relief by
        organization, and a Data dictionary. Numbers keep their formats (pesos, rates, hours).
      </p>
    </div>
  );
}
