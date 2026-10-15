"use client";

export type CsvRow = Record<string, string | number | null | undefined>;

function cell(value: CsvRow[string]): string {
  if (value == null) return "";
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** Downloads the rows behind a chart or table as CSV: raw values, not display formatting. */
export function CsvButton({ filename, columns, rows }: {
  filename: string;
  columns: { key: string; label: string }[];
  rows: CsvRow[];
}) {
  function download() {
    const lines = [
      columns.map((c) => cell(c.label)).join(","),
      ...rows.map((r) => columns.map((c) => cell(r[c.key])).join(",")),
    ];
    // BOM so Excel opens the file as UTF-8 (place names such as Dasmariñas)
    const blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <button
      type="button"
      onClick={download}
      className="shrink-0 rounded-md border border-[var(--border)] px-2.5 py-1 text-sm text-ink-2 hover:text-ink"
    >
      Download CSV
    </button>
  );
}
