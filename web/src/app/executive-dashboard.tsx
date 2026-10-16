"use client";

import { BarList, ColumnChart } from "@/components/charts";
import { CsvButton } from "@/components/csv-button";
import { Card, DataTable, HeroFigure, Legend, PageHeader, StatGrid, StatTile, TableView } from "@/components/ui";
import type { EventSummary, ImpactCubeRow } from "@/lib/data";
import { count, full, peso } from "@/lib/format";
import { useMart } from "@/lib/live";

const COST_SERIES = [
  { key: "housing", label: "Housing", color: "var(--series-1)" },
  { key: "infrastructure", label: "Infrastructure", color: "var(--series-2)" },
  { key: "agriculture", label: "Agriculture", color: "var(--series-3)" },
];

// the events download carries every headline measure, unformatted
const EVENT_CSV_COLUMNS = [
  "event_code", "event_name", "hazard_type", "category", "start_date", "end_date",
  "dead", "injured", "missing", "affected_families", "affected_persons",
  "houses_partially_damaged", "houses_totally_damaged",
  "damage_cost_php", "housing_cost_php", "infrastructure_cost_php", "agriculture_cost_php",
  "peak_persons_in_centers", "centers_used", "relief_value_php", "families_served",
  "response_requests", "median_hours_to_dispatch", "completion_rate",
].map((key) => ({ key, label: key }));

export function ExecutiveDashboard({ eventsSnapshot, cubeSnapshot }: {
  eventsSnapshot: EventSummary[];
  cubeSnapshot: ImpactCubeRow[];
}) {
  // live from the warehouse on XAMPP, the bundled snapshot elsewhere
  const events = [...useMart("mart_event_summary", eventsSnapshot).rows].sort((a, b) =>
    a.start_date.localeCompare(b.start_date),
  );
  const cube = useMart("mart_impact_cube", cubeSnapshot).rows;
  const sum = (f: (e: (typeof events)[number]) => number | null) => events.reduce((t, e) => t + (f(e) ?? 0), 0);
  const totalCost = sum((e) => e.damage_cost_php);
  const worstEvacuation = [...events].sort((a, b) => (b.peak_persons_in_centers ?? 0) - (a.peak_persons_in_centers ?? 0))[0];

  const years = [...new Set(events.map((e) => e.event_year))];
  const costByYear = years.map((y) => {
    const ys = events.filter((e) => e.event_year === y);
    return {
      year: String(y),
      housing: ys.reduce((t, e) => t + e.housing_cost_php, 0),
      infrastructure: ys.reduce((t, e) => t + e.infrastructure_cost_php, 0),
      agriculture: ys.reduce((t, e) => t + e.agriculture_cost_php, 0),
      events: ys.length,
    };
  });

  const topEvents = [...events]
    .sort((a, b) => b.damage_cost_php - a.damage_cost_php)
    .slice(0, 10)
    .map((e) => ({ name: `${e.local_name} ${e.event_year}`, cost: e.damage_cost_php }));

  // ROLAP: region subtotals straight from the GROUP BY CUBE mart
  const byRegion = cube
    .filter((r) => r.grouping_level === "region")
    .sort((a, b) => b.affected_persons - a.affected_persons)
    .slice(0, 10)
    .map((r) => ({ region: r.region_name ?? "", affected: r.affected_persons, cost: r.damage_cost_php }));
  const hazards = cube.filter((r) => r.grouping_level === "hazard");

  return (
    <>
      <PageHeader
        title="Executive overview"
        description="Impact of tropical cyclones and monsoon floods on the Philippines, 2020–2025, across all reporting agencies."
      />

      <div className="grid gap-3 lg:grid-cols-[1fr_2fr]">
        <HeroFigure
          label="Total damage, 2020–2025"
          value={peso(totalCost)}
          detail={`${events.length} events · ${hazards
            .map((h) => `${h.events} ${h.hazard_type === "Flood" ? "monsoon floods" : "tropical cyclones"}`)
            .join(", ")}`}
        />
        <StatGrid>
          <StatTile label="Deaths" value={full(sum((e) => e.dead))} detail={`${full(sum((e) => e.missing))} missing`} />
          <StatTile label="People affected" value={count(sum((e) => e.affected_persons))} />
          <StatTile label="Houses destroyed" value={count(sum((e) => e.houses_totally_damaged))} />
          <StatTile
            label="Peak in evacuation centers"
            value={count(worstEvacuation.peak_persons_in_centers)}
            detail={worstEvacuation.event_name}
          />
          <StatTile label="Relief delivered" value={peso(sum((e) => e.relief_value_php))} />
          <StatTile label="Response requests" value={count(sum((e) => e.response_requests))} />
        </StatGrid>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Damage cost by year" subtitle="Stacked by damage category">
          <Legend items={COST_SERIES} />
          <ColumnChart data={costByYear} xKey="year" series={COST_SERIES} format="peso" />
          <TableView
            columns={[
              { key: "year", label: "Year" },
              { key: "events", label: "Events", numeric: true },
              ...COST_SERIES.map((s) => ({ key: s.key, label: s.label, numeric: true })),
            ]}
            rows={costByYear.map((r) => ({
              year: r.year,
              events: r.events,
              housing: peso(r.housing),
              infrastructure: peso(r.infrastructure),
              agriculture: peso(r.agriculture),
            }))}
            csv={{ filename: "damage-cost-by-year-php", rows: costByYear }}
          />
        </Card>

        <Card title="Costliest events" subtitle="Total damage cost, top 10">
          <BarList
            data={topEvents}
            labelKey="name"
            series={[{ key: "cost", label: "Damage cost", color: "var(--series-1)" }]}
            format="peso"
            labelWidth={120}
          />
          <TableView
            columns={[{ key: "name", label: "Event" }, { key: "cost", label: "Damage cost", numeric: true }]}
            rows={topEvents.map((r) => ({ name: r.name, cost: peso(r.cost) }))}
            csv={{ filename: "costliest-events-php", rows: topEvents }}
          />
        </Card>

        <Card
          title="People affected by region"
          subtitle="Top 10 regions, all events · region subtotals from the GROUP BY CUBE mart"
          className="lg:col-span-2"
        >
          <BarList
            data={byRegion}
            labelKey="region"
            series={[{ key: "affected", label: "People affected", color: "var(--series-1)" }]}
            format="count"
            labelWidth={190}
          />
          <TableView
            columns={[
              { key: "region", label: "Region" },
              { key: "affected", label: "People affected", numeric: true },
              { key: "cost", label: "Damage cost", numeric: true },
            ]}
            rows={byRegion.map((r) => ({ region: r.region, affected: full(r.affected), cost: peso(r.cost) }))}
            csv={{ filename: "people-affected-by-region", rows: byRegion }}
          />
        </Card>
      </div>

      <Card title="All events" subtitle="One row per event, newest first" className="mt-4">
        <div className="mb-3 flex justify-end">
          <CsvButton filename="driw-events" columns={EVENT_CSV_COLUMNS} rows={[...events].reverse()} />
        </div>
        <div className="max-h-[28rem] overflow-auto">
          <DataTable
            columns={[
              { key: "event", label: "Event" },
              { key: "category", label: "Category" },
              { key: "dates", label: "Dates" },
              { key: "dead", label: "Deaths", numeric: true },
              { key: "affected", label: "Affected", numeric: true },
              { key: "cost", label: "Damage", numeric: true },
              { key: "relief", label: "Relief", numeric: true },
            ]}
            rows={[...events].reverse().map((e) => ({
              event: e.event_name,
              category: e.category,
              dates: `${e.start_date} – ${e.end_date}`,
              dead: full(e.dead),
              affected: count(e.affected_persons),
              cost: peso(e.damage_cost_php),
              relief: peso(e.relief_value_php),
            }))}
          />
        </div>
      </Card>
    </>
  );
}
