"use client";

import { BarList, ColumnChart, GroupedColumns, TrendArea } from "@/components/charts";
import { EventSelect } from "@/components/event-select";
import { Card, Legend, StatGrid, StatTile, TableView } from "@/components/ui";
import type { DisplacementDay, EvacuationDay, EventSummary, LifelineRestoration, ResponsePerformance } from "@/lib/data";
import { count, full, hours, percent, shortDate } from "@/lib/format";
import { useMart } from "@/lib/live";
import { useEventParam } from "@/lib/use-event-param";

const PRIORITY_SERIES = [
  { key: "P1", label: "P1 (critical)", color: "var(--series-1)" },
  { key: "P2", label: "P2 (urgent)", color: "var(--series-2)" },
  { key: "P3", label: "P3 (routine)", color: "var(--series-3)" },
];

const DISPLACED_SERIES = [
  { key: "inside", label: "In evacuation centers", color: "var(--series-1)" },
  { key: "outside", label: "With relatives or friends", color: "var(--series-2)" },
];

const RESTORE_SERIES = [
  { key: "fast", label: "Restored within 72 h", color: "var(--series-1)" },
  { key: "slow", label: "Restored later", color: "var(--series-2)" },
  { key: "down", label: "Still down", color: "var(--series-3)" },
];

// short axis labels so five categories fit on a phone; the table keeps the full names
const SHORT_LIFELINE: Record<string, string> = {
  ROAD: "Roads", BRIDGE: "Bridges", POWER: "Power", WATER: "Water", COMMS: "Communications",
};
const SHORT_TYPE: Record<string, string> = {
  "Evacuation assistance": "Evac",
  "Medical evacuation": "Medevac",
  "Relief delivery": "Relief",
  "Road clearing": "Roads",
  "Search and rescue": "Rescue",
};

export function OperationsDashboard({
  events: eventsSnapshot, evacuation: evacuationSnapshot, displacement: displacementSnapshot,
  lifelines: lifelinesSnapshot, response: responseSnapshot, options, initial,
}: {
  events: EventSummary[];
  evacuation: EvacuationDay[];
  displacement: DisplacementDay[];
  lifelines: LifelineRestoration[];
  response: ResponsePerformance[];
  options: { code: string; label: string }[];
  initial: string;
}) {
  // live from the warehouse on XAMPP, the bundled snapshot elsewhere
  const events = useMart("mart_event_summary", eventsSnapshot).rows;
  const evacuation = useMart("mart_evacuation_daily", evacuationSnapshot).rows;
  const displacement = useMart("mart_displacement_daily", displacementSnapshot).rows;
  const lifelines = useMart("mart_lifeline_restoration", lifelinesSnapshot).rows;
  const response = useMart("mart_response_performance", responseSnapshot).rows.filter((r) => r.event_code !== "All");
  const [code, setCode] = useEventParam(options.map((o) => o.code), initial);
  const event = events.find((e) => e.event_code === code)!;
  const days = evacuation.filter((d) => d.event_code === code).sort((a, b) => a.snapshot_date.localeCompare(b.snapshot_date));
  const rows = response.filter((r) => r.event_code === code);
  const displaced = displacement
    .filter((d) => d.event_code === code)
    .sort((a, b) => a.snapshot_date.localeCompare(b.snapshot_date));
  const lifelineRows = lifelines.filter((l) => l.event_code === code);
  const restoration = lifelineRows.map((l) => ({
    lifeline: SHORT_LIFELINE[l.lifeline_code] ?? l.lifeline_name,
    fast: l.restored_within_72h,
    slow: l.places_restored - l.restored_within_72h,
    down: l.places_still_down,
  }));

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
        <StatTile label="Peak displaced" value={count(event.peak_persons_displaced)} detail="inside + outside centers, busiest day" />
        <StatTile label="Peak in evacuation centers" value={count(event.peak_persons_in_centers)} detail={`${full(event.centers_used)} centers used`} />
        <StatTile
          label="Over-capacity center-days"
          value={full(event.over_capacity_center_days)}
          detail="families exceeded capacity"
        />
        <StatTile label="Response requests" value={full(event.response_requests)} />
        <StatTile label="Median time to dispatch" value={hours(event.median_hours_to_dispatch)} />
        <StatTile
          label="Lifelines disrupted"
          value={full(event.lifeline_disruptions)}
          detail={`median ${hours(event.median_hours_to_restore)} to restore · ${full(event.lifelines_still_down)} still down`}
        />
      </StatGrid>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card
          title="People displaced, inside and outside evacuation centers"
          subtitle="Per day · most displaced families stay with relatives or friends (DSWD DROMIC)"
          className="lg:col-span-2"
        >
          <Legend items={DISPLACED_SERIES} />
          <ColumnChart
            data={displaced.map((d) => ({ date: shortDate(d.snapshot_date), inside: d.persons_inside, outside: d.persons_outside }))}
            xKey="date"
            series={DISPLACED_SERIES}
            format="count"
          />
          <TableView
            columns={[
              { key: "date", label: "Date" },
              { key: "inside", label: "In centers", numeric: true },
              { key: "outside", label: "Outside centers", numeric: true },
              { key: "total", label: "Total displaced", numeric: true },
              { key: "share", label: "Share outside", numeric: true },
            ]}
            rows={displaced.map((d) => ({
              date: shortDate(d.snapshot_date),
              inside: full(d.persons_inside),
              outside: full(d.persons_outside),
              total: full(d.persons_displaced),
              share: percent(d.share_outside_centers, 0),
            }))}
            csv={{
              filename: `displacement-daily-${code}`,
              rows: displaced.map((d) => ({
                date: d.snapshot_date, inside: d.persons_inside, outside: d.persons_outside,
                total: d.persons_displaced, share_outside: d.share_outside_centers,
              })),
            }}
          />
        </Card>

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
            csv={{
              filename: `evacuation-daily-${code}`,
              rows: days.map((d) => ({
                date: d.snapshot_date, centers: d.centers_open, persons: d.persons_inside,
                families: d.families_inside, occ: d.occupancy_rate,
              })),
            }}
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
            csv={{
              filename: `centers-over-capacity-${code}`,
              rows: days.map((d) => ({ date: d.snapshot_date, over: d.centers_over_capacity, open: d.centers_open })),
            }}
          />
        </Card>

        <Card
          title="Lifelines: roads, bridges, power, water, communications"
          subtitle="Cities and municipalities where each lifeline went down, by how fast service came back"
          className="lg:col-span-2"
        >
          {restoration.length === 0 ? (
            <p className="text-sm text-ink-2">No lifeline disruptions were reported for this event.</p>
          ) : (
            <>
              <Legend items={RESTORE_SERIES} />
              <BarList data={restoration} labelKey="lifeline" series={RESTORE_SERIES} format="count" labelWidth={120} />
              <TableView
                columns={[
                  { key: "lifeline", label: "Lifeline" },
                  { key: "places", label: "Places disrupted", numeric: true },
                  { key: "units", label: "Units affected", numeric: true },
                  { key: "median", label: "Median to restore", numeric: true },
                  { key: "p90", label: "90th pct", numeric: true },
                  { key: "down", label: "Still down", numeric: true },
                ]}
                rows={lifelineRows.map((l) => ({
                  lifeline: l.lifeline_name,
                  places: full(l.places_disrupted),
                  units: `${full(l.units_affected)} ${l.unit_of_measure}`,
                  median: hours(l.median_hours_to_restore),
                  p90: hours(l.p90_hours_to_restore),
                  down: full(l.places_still_down),
                }))}
                csv={{ filename: `lifelines-${code}`, rows: lifelineRows }}
              />
            </>
          )}
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
            csv={{
              filename: `response-times-hours-${code}`,
              rows: typeTotals.map((r) => ({
                type: r.response_type, requests: r.requests, dispatch: r.median_hours_to_dispatch,
                p90: r.p90_hours_to_dispatch, arrive: r.median_hours_to_arrive, done: r.completion_rate,
              })),
            }}
          />
        </Card>
      </div>
    </>
  );
}
