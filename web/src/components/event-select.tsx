"use client";

export function EventSelect({ value, options, onChange, allLabel }: {
  value: string;
  options: { code: string; label: string }[];
  onChange: (code: string) => void;
  allLabel?: string;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <label htmlFor="event" className="text-sm text-ink-2">
        Event
      </label>
      <select
        id="event"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-w-0 max-w-full rounded-md border border-[var(--border)] bg-surface px-3 py-1.5 text-sm"
      >
        {allLabel && <option value="ALL">{allLabel}</option>}
        {options.map((o) => (
          <option key={o.code} value={o.code}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
