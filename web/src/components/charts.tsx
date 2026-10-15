"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { count, hours, peso, percent, shortDate } from "@/lib/format";

export type Series = { key: string; label: string; color: string };
// Formatters are chosen by name: server components cannot pass functions to client components.
const FORMATS = { peso, count, hours, percent: (v: number) => percent(v, 0) } as const;
export type FormatName = keyof typeof FORMATS;
type Fmt = (v: number) => string;

const axisTick = { fill: "var(--muted)", fontSize: 12 };
const ANIMATION_MS = 400;
const ROUNDED_END_V: [number, number, number, number] = [4, 4, 0, 0]; // columns: rounded top
const ROUNDED_END_H: [number, number, number, number] = [0, 4, 4, 0]; // bars: rounded right end

type TipEntry = { name?: string; value?: number; color?: string; dataKey?: string | number };

/** Tooltip: value leads (strong), series name follows; keyed by a short line of the series colour. */
function Tip({ active, payload, label, format, labelFormat }: {
  active?: boolean;
  payload?: TipEntry[];
  label?: string | number;
  format: Fmt;
  labelFormat?: (l: string) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-[var(--border)] bg-surface px-3 py-2 text-sm shadow-lg">
      <p className="mb-1 text-ink-2">{labelFormat ? labelFormat(String(label)) : label}</p>
      {[...payload].reverse().map((p) => (
        <p key={String(p.dataKey)} className="flex items-center gap-2">
          <span aria-hidden className="h-0.5 w-3 rounded" style={{ background: p.color }} />
          <strong className="tabular font-semibold">{format(Number(p.value))}</strong>
          {payload.length > 1 && <span className="text-ink-2">{p.name}</span>}
        </p>
      ))}
    </div>
  );
}

/** Vertical columns, stacked when there are several series (2px surface gap between segments). */
export function ColumnChart({ data, xKey, series, format, height = 280 }: {
  data: Record<string, string | number | null>[];
  xKey: string;
  series: Series[];
  format: FormatName;
  height?: number;
}) {
  const fmt = FORMATS[format];
  const stacked = series.length > 1;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--grid)" />
        <XAxis dataKey={xKey} tick={axisTick} tickLine={false} axisLine={{ stroke: "var(--baseline)" }} />
        <YAxis tick={axisTick} tickLine={false} axisLine={false} tickFormatter={fmt} width={64} />
        <Tooltip cursor={{ fill: "var(--grid)", opacity: 0.4 }} content={<Tip format={fmt} />} />
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            stackId={stacked ? "stack" : undefined}
            fill={s.color}
            maxBarSize={24}
            animationDuration={ANIMATION_MS}
            stroke="var(--surface)"
            strokeWidth={stacked ? 2 : 0}
            radius={!stacked || i === series.length - 1 ? ROUNDED_END_V : 0}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Horizontal bars, sorted by the caller; value label at each bar's tip. Optionally stacked. */
export function BarList({ data, labelKey, series, format, labelWidth = 150 }: {
  data: Record<string, string | number | null>[];
  labelKey: string;
  series: Series[];
  format: FormatName;
  labelWidth?: number;
}) {
  const fmt = FORMATS[format];
  const stacked = series.length > 1;
  const height = Math.max(120, data.length * 32 + 24);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: stacked ? 16 : 64, left: 0, bottom: 0 }}>
        <CartesianGrid horizontal={false} stroke="var(--grid)" />
        <XAxis type="number" tick={axisTick} tickLine={false} axisLine={false} tickFormatter={fmt} />
        <YAxis
          type="category"
          dataKey={labelKey}
          width={labelWidth}
          tick={{ ...axisTick, fill: "var(--ink-2)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--baseline)" }}
          interval={0}
        />
        <Tooltip cursor={{ fill: "var(--grid)", opacity: 0.4 }} content={<Tip format={fmt} />} />
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            stackId={stacked ? "stack" : undefined}
            fill={s.color}
            maxBarSize={20}
            animationDuration={ANIMATION_MS}
            stroke="var(--surface)"
            strokeWidth={stacked ? 2 : 0}
            radius={!stacked || i === series.length - 1 ? ROUNDED_END_H : 0}
          >
            {!stacked && (
              <LabelList
                dataKey={s.key}
                position="right"
                formatter={(v: unknown) => fmt(Number(v))}
                style={{ fill: "var(--ink-2)", fontSize: 12 }}
              />
            )}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Grouped columns: several comparable measures side by side (same unit, one axis). */
export function GroupedColumns({ data, xKey, series, format, height = 280 }: {
  data: Record<string, string | number | null>[];
  xKey: string;
  series: Series[];
  format: FormatName;
  height?: number;
}) {
  const fmt = FORMATS[format];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={2}>
        <CartesianGrid vertical={false} stroke="var(--grid)" />
        <XAxis dataKey={xKey} tick={axisTick} tickLine={false} axisLine={{ stroke: "var(--baseline)" }} interval={0} />
        <YAxis tick={axisTick} tickLine={false} axisLine={false} tickFormatter={fmt} width={56} />
        <Tooltip cursor={{ fill: "var(--grid)", opacity: 0.4 }} content={<Tip format={fmt} />} />
        {series.map((s) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            fill={s.color}
            maxBarSize={20}
            radius={ROUNDED_END_V}
            animationDuration={ANIMATION_MS}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Single-series trend: 2px line over a 10% wash, crosshair tooltip. */
export function TrendArea({ data, xKey, yKey, label, color, format, xFormat, height = 260 }: {
  data: Record<string, string | number | null>[];
  xKey: string;
  yKey: string;
  label: string;
  color: string;
  format: FormatName;
  xFormat?: "shortDate";
  height?: number;
}) {
  const fmt = FORMATS[format];
  const xFmt = xFormat === "shortDate" ? shortDate : undefined;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--grid)" />
        <XAxis
          dataKey={xKey}
          tick={axisTick}
          tickLine={false}
          axisLine={{ stroke: "var(--baseline)" }}
          tickFormatter={xFmt}
          minTickGap={24}
        />
        <YAxis tick={axisTick} tickLine={false} axisLine={false} tickFormatter={fmt} width={56} />
        <Tooltip
          cursor={{ stroke: "var(--muted)", strokeWidth: 1 }}
          content={<Tip format={fmt} labelFormat={xFmt} />}
        />
        <Area
          type="monotone"
          dataKey={yKey}
          name={label}
          stroke={color}
          strokeWidth={2}
          fill={color}
          fillOpacity={0.1}
          animationDuration={ANIMATION_MS}
          activeDot={{ r: 5, stroke: "var(--surface)", strokeWidth: 2, fill: color }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
