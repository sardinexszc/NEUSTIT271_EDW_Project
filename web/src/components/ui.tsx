import type { ReactNode } from "react";
import { CsvButton, type CsvRow } from "./csv-button";

export function PageHeader({ title, description }: { title: string; description: string }) {
  return (
    <header className="mb-6">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
      <p className="mt-1 max-w-3xl text-ink-2">{description}</p>
    </header>
  );
}

export function Card({ title, subtitle, children, className = "" }: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`min-w-0 rounded-xl border border-[var(--border)] bg-surface p-4 sm:p-5 ${className}`}>
      <h2 className="font-semibold">{title}</h2>
      {subtitle && <p className="mt-0.5 text-sm text-ink-2">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function HeroFigure({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-surface p-5">
      <p className="text-sm text-ink-2">{label}</p>
      <p className="mt-1 text-5xl font-semibold tracking-tight">{value}</p>
      {detail && <p className="mt-2 text-sm text-ink-2">{detail}</p>}
    </div>
  );
}

export function StatTile({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-surface p-4">
      <p className="text-sm text-ink-2">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {detail && <p className="mt-1 text-xs text-muted">{detail}</p>}
    </div>
  );
}

export function StatGrid({ children }: { children: ReactNode }) {
  return <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">{children}</div>;
}

export type LegendItem = { label: string; color: string; shape?: "rect" | "line" };

export function Legend({ items }: { items: LegendItem[] }) {
  return (
    <ul className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-2">
      {items.map((i) => (
        <li key={i.label} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className={i.shape === "line" ? "h-0.5 w-4 rounded" : "h-3 w-3 rounded-sm"}
            style={{ background: i.color }}
          />
          {i.label}
        </li>
      ))}
    </ul>
  );
}

/** Every chart has a table twin: the accessible, colour-free way to read every value.
    `csv` (raw values keyed like `columns`) adds a download of the same rows. */
export function TableView({ columns, rows, csv }: {
  columns: { key: string; label: string; numeric?: boolean }[];
  rows: Record<string, ReactNode>[];
  csv?: { filename: string; rows: CsvRow[] };
}) {
  return (
    <div className="mt-3 flex items-start gap-3 text-sm">
      <details className="min-w-0 flex-1">
        <summary className="cursor-pointer text-ink-2 hover:text-ink">Show table</summary>
        <div className="mt-2 max-h-80 overflow-auto rounded-md border border-[var(--border)]">
          <DataTable columns={columns} rows={rows} />
        </div>
      </details>
      {csv && <CsvButton filename={csv.filename} columns={columns} rows={csv.rows} />}
    </div>
  );
}

export function DataTable({ columns, rows }: {
  columns: { key: string; label: string; numeric?: boolean }[];
  rows: Record<string, ReactNode>[];
}) {
  return (
    <table className="w-full text-left text-sm">
      <thead className="sticky top-0 bg-surface text-ink-2">
        <tr>
          {columns.map((c) => (
            <th key={c.key} scope="col" className={`border-b border-[var(--border)] px-3 py-2 font-medium ${c.numeric ? "text-right" : ""}`}>
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className="border-b border-[var(--border)] last:border-0">
            {columns.map((c) => (
              <td key={c.key} className={`px-3 py-1.5 ${c.numeric ? "tabular text-right" : ""}`}>
                {r[c.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
