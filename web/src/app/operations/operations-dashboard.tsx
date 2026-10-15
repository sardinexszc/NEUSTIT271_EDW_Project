"use client";

import { useState } from "react";
import { ColumnChart, GroupedColumns, TrendArea } from "@/components/charts";
import { EventSelect } from "@/components/event-select";
import { Card, Legend, StatGrid, StatTile, TableView } from "@/components/ui";
import type { EvacuationDay, EventSummary, ResponsePerformance } from "@/lib/data";
import { count, full, hours, percent, shortDate } from "@/lib/format";

const PRIORITY_SERIES = [
  { key: "P1", label: "P1 (critical)", color: "var(--series-1)" },
  { key: "P2", label: "P2 (urgent)", color: "var(--series-2)" },
  { key: "P3", label: "P3 (routine)", color: "var(--series-3)" },
];

// short axis labels so five categories fit on a phone; the table keeps the full names
const SHORT_TYPE: Record<string, string> = {
  "Evacuation assistance": "Evac",
  "Medical evacuation": "Medevac",
  "Relief delivery": "Relief",
  "Road clearing": "Roads",
  "Search and rescue": "Rescue",
};

export function OperationsDashboard({ events, evacuation, response, options, initial }: {
  events: EventSummary[];
  evacuation: EvacuationDay[];
  response: ResponsePerformance[];
  options: { code: string; label: string }[];
  initial: string;
}) {
  const [code, setCode] = useState(initial);
  const event = events.find((e) => e.event_code === code)!;
  const days = evacuation.filter((d) => d.event_code === code).sort((a, b) => a.snapshot_date.localeCompare(b.snapshot_date));
  const rows = response.filter((r) => r.event_code === code);

  const types = [...new Set(rows.filter((r) => r.response_type !== "All").map((r) => r.response_type))];
  const dispatchByType = types.map((t) => {
    const row: Record<string, string | number | null> = { type: SHORT_TYPE[t] ?? t };
    for (const p of PRIORITY_SERIES) {
      row[p.key] = rows.find((r) => r.response_type === t && r.priority === p.key)?.median_hours_to_dispatch ?? null;
    }
    return row;
  });
  const typeTotals = rows.filter((r) => r.response_type !== "All" && r.priority === "All");

  return (
    <>
      <EventSelect value={code} options={options} onChange={setCode} />

      <StatGrid>
        <StatTile label="Peak in evacuation centers" value={count(event.peak_persons_in_centers)} detail="persons, busiest day" />
        <StatTile label="Evacuation centers used" value={full(event.centers_used)} />
        <StatTile
          label="Over-capacity center-days"
          value={full(event.over_capacity_center_days)}
          detail="families exceeded capacity"
        />
        <StatTile label="Response requests" value={full(event.response_requests)} />
        <StatTile label="Median time to dispatch" value={hours(event.median_hours_to_dispatch)} />
        <StatTile label="Requests completed" value={percent(event.completion_rate)} />
      </StatGrid>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="People in evacuation centers" subtitle="Total across all open centers, per day">
          <TrendArea
            data={days}
            xKey="snapshot_date"
            yKey="persons_inside"
            label="Persons inside"
            color="var(--series-1)"
            format="count"
            xFormat="shortDate"
          />
          <TableView
            columns={[
              { key: "date", label: "Date" },
              { key: "centers", label: "Centers open", numeric: true },
              { key: "persons", label: "Persons", numeric: true },
              { key: "families", label: "Families", numeric: true },
              { key: "occ", label: "Occupancy", numeric: true },
            ]}
            rows={days.map((d) => ({
              date: shortDate(d.snapshot_date),
              centers: full(d.centers_open),
              persons: full(d.persons_inside),
              families: full(d.families_inside),
              occ: percent(d.occupancy_rate, 0),
            }))}
          />
        </Card>

        <Card title="Centers over capacity" subtitle="Number of centers where families exceeded capacity, per day">
          <ColumnChart
            data={days.map((d) => ({ date: shortDate(d.snapshot_date), over: d.centers_over_capacity }))}
            xKey="date"
            series={[{ key: "over", label: "Centers over capacity", color: "var(--series-1)" }]}
            format="count"
            height={260}
          />
          <TableView
            columns={[
              { key: "date", label: "Date" },
              { key: "over", label: "Over capacity", numeric: true },
              { key: "open", label: "Open", numeric: true },
            ]}
            rows={days.map((d) => ({
              date: shortDate(d.snapshot_date),
              over: full(d.centers_over_capacity),
              open: full(d.centers_open),
            }))}
          />
        </Card>

        <Card
          title="Median time to dispatch"
          subtitle="By response type and priority · hours from request to dispatch"
          className="lg:col-span-2"
        >
          <Legend items={PRIORITY_SERIES} />
          <GroupedColumns data={dispatchByType} xKey="type" series={PRIORITY_SERIES} format="hours" />
          <TableView
            columns={[
              { key: "type", label: "Response type" },
              { key: "requests", label: "Requests", numeric: true },
              { key: "dispatch", label: "Median dispatch", numeric: true },
              { key: "p90", label: "90th pct dispatch", numeric: true },
              { key: "arrive", label: "Median travel", numeric: true },
              { key: "done", label: "Completed", numeric: true },
            ]}
            rows={typeTotals.map((r) => ({
              type: r.response_type,
              requests: full(r.requests),
              dispatch: hours(r.median_hours_to_dispatch),
              p90: hours(r.p90_hours_to_dispatch),
              arrive: hours(r.median_hours_to_arrive),
              done: percent(r.completion_rate),
            }))}
          />
        </Card>
      </div>
    </>
  );
}
