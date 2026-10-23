import { BarList, ColumnChart } from "@/components/charts";
import { CsvButton } from "@/components/csv-button";
import { Card, DataTable, HeroFigure, Legend, PageHeader, StatGrid, StatTile, TableView } from "@/components/ui";
import { cube, events } from "@/lib/data";
import { count, full, percent, peso } from "@/lib/format";

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
  "affected_area_population", "dead_per_100k", "missing_per_100k", "affected_per_100k", "dead_per_100k_national",
  "peak_persons_in_centers", "peak_persons_outside_centers", "peak_persons_displaced", "centers_used",
  "relief_value_php", "relief_national_government_php", "relief_lgu_php", "relief_ngo_php", "relief_international_php",
  "families_served", "response_requests", "median_hours_to_dispatch", "completion_rate",
  "lifeline_disruptions", "lifelines_still_down", "median_hours_to_restore",
].map((key) => ({ key, label: key }));

export default function ExecutivePage() {
  const sum = (f: (e: (typeof events)[number]) => number | null) => events.reduce((t, e) => t + (f(e) ?? 0), 0);
  const totalCost = sum((e) => e.damage_cost_php);
  const worstDisplacement = [...events].sort((a, b) => (b.peak_persons_displaced ?? 0) - (a.peak_persons_displaced ?? 0))[0];
  // Sendai target A: deaths per 100,000 people, so a small event that hit hard is not hidden
  // behind big events; denominator = population of the places that reported damage
  const deadliest = [...events]
    .filter((e) => e.dead_per_100k != null)
    .sort((a, b) => (b.dead_per_100k ?? 0) - (a.dead_per_100k ?? 0))
    .slice(0, 10)
    .map((e) => ({
      name: `${e.local_name} ${e.event_year}`,
      rate: e.dead_per_100k ?? 0,
      dead: e.dead,
      population: e.affected_area_population ?? 0,
    }));

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
            label="Peak displaced"
            value={count(worstDisplacement.peak_persons_displaced)}
            detail={`${worstDisplacement.local_name} · ${percent(
              (worstDisplacement.peak_persons_outside_centers ?? 0) / Math.max(1, worstDisplacement.peak_persons_displaced ?? 0),
              0,
            )} outside centers`}
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
          title="Deaths per 100,000 people"
          subtitle="Top 10 events · population of the cities and municipalities that reported damage"
          className="lg:col-span-2"
        >
          <BarList
            data={deadliest}
            labelKey="name"
            series={[{ key: "rate", label: "Deaths per 100,000", color: "var(--series-1)" }]}
            format="count"
            labelWidth={120}
          />
          <p className="mt-2 text-xs text-muted">
            Sendai Framework target A. Populations are estimates (barangay count × 2,600), so compare events, not absolute rates.
          </p>
          <TableView
            columns={[
              { key: "name", label: "Event" },
              { key: "dead", label: "Deaths", numeric: true },
              { key: "population", label: "Population of affected places", numeric: true },
              { key: "rate", label: "Per 100,000", numeric: true },
            ]}
            rows={deadliest.map((r) => ({
              name: r.name, dead: full(r.dead), population: full(r.population), rate: r.rate.toFixed(2),
            }))}
            csv={{ filename: "deaths-per-100k", rows: deadliest }}
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
              { key: "rate", label: "Deaths /100k", numeric: true },
              { key: "affected", label: "Affected", numeric: true },
              { key: "cost", label: "Damage", numeric: true },
              { key: "relief", label: "Relief", numeric: true },
            ]}
            rows={[...events].reverse().map((e) => ({
              event: e.event_name,
              category: e.category,
              dates: `${e.start_date} – ${e.end_date}`,
              dead: full(e.dead),
              rate: e.dead_per_100k == null ? "–" : e.dead_per_100k.toFixed(2),
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
