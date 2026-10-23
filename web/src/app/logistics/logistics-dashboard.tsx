"use client";

import { BarList } from "@/components/charts";
import { EventSelect } from "@/components/event-select";
import { CsvButton } from "@/components/csv-button";
import { Card, DataTable, Legend, StatGrid, StatTile, TableView } from "@/components/ui";
import type { ProvinceImpact, ReliefByOrg } from "@/lib/data";
import { count, full, percent, peso } from "@/lib/format";
import { useEventParam } from "@/lib/use-event-param";

// Fixed order = fixed colour per category, whatever the filter shows.
const CATEGORY_SERIES = [
  { key: "Food", label: "Food", color: "var(--series-1)" },
  { key: "Non-Food", label: "Non-food", color: "var(--series-2)" },
  { key: "Water", label: "Water", color: "var(--series-3)" },
  { key: "Shelter", label: "Shelter", color: "var(--series-4)" },
  { key: "Medical", label: "Medical", color: "var(--series-5)" },
];

// DROMIC reports the cost of assistance by who provided it
const PROVIDERS = [
  { key: "National Government", label: "National government (DSWD)" },
  { key: "LGU", label: "Local government units" },
  { key: "NGO", label: "NGOs" },
  { key: "International", label: "International (UN)" },
];

export function LogisticsDashboard({ relief, provinces, options }: {
  relief: ReliefByOrg[];
  provinces: ProvinceImpact[];
  options: { code: string; label: string }[];
}) {
  const [code, setCode] = useEventParam(options.map((o) => o.code), "ALL");
  const inScope = <T extends { event_code: string }>(rows: T[]) =>
    code === "ALL" ? rows : rows.filter((r) => r.event_code === code);
  const scopeName = code === "ALL" ? "all-events" : code;
  const reliefRows = inScope(relief);
  const provinceRows = inScope(provinces);

  const totalValue = reliefRows.reduce((t, r) => t + r.relief_value_php, 0);
  const familiesServed = reliefRows.reduce((t, r) => t + r.families_served, 0);
  const distributions = reliefRows.reduce((t, r) => t + r.distributions, 0);
  const affectedPersons = provinceRows.reduce((t, r) => t + r.affected_persons, 0);
  const affectedFamilies = provinceRows.reduce((t, r) => t + r.affected_families, 0);

  const byProvider = PROVIDERS.map((p) => {
    const rows = reliefRows.filter((r) => r.org_type === p.key);
    const value = rows.reduce((t, r) => t + r.relief_value_php, 0);
    return { provider: p.label, value, share: value / Math.max(1, totalValue), families: rows.reduce((t, r) => t + r.families_served, 0) };
  });

  // short codes keep the bar labels on one line; the table shows full names
  const shortName = (code: string) => (code === "CARITAS" ? "Caritas" : code);
  const orgs = [...new Map(reliefRows.map((r) => [r.org_code, r.org_name])).entries()];
  const byOrg = orgs
    .map(([orgCode, orgName]) => {
      const row: Record<string, string | number> = { org: shortName(orgCode), orgName, total: 0 };
      for (const c of CATEGORY_SERIES) {
        const v = reliefRows
          .filter((r) => r.org_code === orgCode && r.resource_category === c.key)
          .reduce((t, r) => t + r.relief_value_php, 0);
        row[c.key] = v;
        row.total = (row.total as number) + v;
      }
      return row;
    })
    .sort((a, b) => (b.total as number) - (a.total as number));

  // combine event x province rows into one row per province for the selected scope
  const provinceMap = new Map<string, { province: string; region: string; affected: number; families: number; value: number; served: number }>();
  for (const r of provinceRows) {
    const p = provinceMap.get(r.province_name) ?? {
      province: r.province_name, region: r.region_name, affected: 0, families: 0, value: 0, served: 0,
    };
    p.affected += r.affected_persons;
    p.families += r.affected_families;
    p.value += r.relief_value_php;
    p.served += r.families_served;
    provinceMap.set(r.province_name, p);
  }
  const coverage = [...provinceMap.values()]
    .filter((p) => p.affected > 0)
    .map((p) => ({ ...p, perPerson: p.value / p.affected, familyCoverage: p.served / Math.max(1, p.families) }))
    .sort((a, b) => a.perPerson - b.perPerson);
  const leastServed = coverage.slice(0, 10).map((p) => ({ province: p.province, perPerson: Math.round(p.perPerson) }));

  return (
    <>
      <EventSelect value={code} options={options} onChange={setCode} allLabel="All events, 2020–2025" />

      <StatGrid>
        <StatTile label="Relief delivered" value={peso(totalValue)} />
        <StatTile label="Family servings" value={count(familiesServed)} detail="a family can be served more than once" />
        <StatTile label="Distributions" value={full(distributions)} />
        <StatTile label="Relief per affected person" value={peso(totalValue / Math.max(1, affectedPersons))} />
        <StatTile
          label="Servings per affected family"
          value={(familiesServed / Math.max(1, affectedFamilies)).toFixed(2)}
          detail="family servings ÷ affected families"
        />
        <StatTile label="Provinces reached" value={full(coverage.filter((p) => p.value > 0).length)} />
      </StatGrid>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Relief value by organization" subtitle="Stacked by resource category, standard units valued at PHP">
          <Legend items={CATEGORY_SERIES} />
          <BarList data={byOrg} labelKey="org" series={CATEGORY_SERIES} format="peso" labelWidth={70} />
          <TableView
            columns={[{ key: "org", label: "Organization" }, ...CATEGORY_SERIES.map((c) => ({ key: c.key, label: c.label, numeric: true })), { key: "total", label: "Total", numeric: true }]}
            rows={byOrg.map((r) => ({
              org: `${r.orgName} (${r.org})`,
              ...Object.fromEntries(CATEGORY_SERIES.map((c) => [c.key, peso(r[c.key] as number)])),
              total: peso(r.total as number),
            }))}
            csv={{
              filename: `relief-by-organization-php-${scopeName}`,
              rows: byOrg.map((r) => ({ ...r, org: `${r.orgName} (${r.org})` })),
            }}
          />
        </Card>

        <Card title="Cost of assistance by provider" subtitle="Who paid for the relief delivered (DSWD DROMIC breakdown)">
          <BarList
            data={byProvider}
            labelKey="provider"
            series={[{ key: "value", label: "Relief value", color: "var(--series-1)" }]}
            format="peso"
            labelWidth={190}
          />
          <TableView
            columns={[
              { key: "provider", label: "Provider" },
              { key: "value", label: "Relief value", numeric: true },
              { key: "share", label: "Share", numeric: true },
              { key: "families", label: "Family servings", numeric: true },
            ]}
            rows={byProvider.map((p) => ({
              provider: p.provider, value: peso(p.value), share: percent(p.share, 0), families: full(p.families),
            }))}
            csv={{ filename: `cost-of-assistance-by-provider-php-${scopeName}`, rows: byProvider }}
          />
        </Card>

        <Card title="Least-served provinces" subtitle="Relief value per affected person, lowest 10" className="lg:col-span-2">
          <BarList
            data={leastServed}
            labelKey="province"
            series={[{ key: "perPerson", label: "PHP per affected person", color: "var(--series-1)" }]}
            format="peso"
            labelWidth={150}
          />
          <p className="mt-2 text-xs text-muted">
            Low values flag provinces where relief lagged behind impact: candidates for re-allocation.
          </p>
        </Card>
      </div>

      <Card title="Relief coverage by province" subtitle="Sorted from least to most relief per affected person" className="mt-4">
        <div className="mb-3 flex justify-end">
          <CsvButton
            filename={`relief-coverage-by-province-${scopeName}`}
            columns={[
              { key: "province", label: "Province" },
              { key: "region", label: "Region" },
              { key: "affected", label: "People affected" },
              { key: "value", label: "Relief value (PHP)" },
              { key: "perPerson", label: "PHP per affected person" },
              { key: "familyCoverage", label: "Servings per affected family" },
            ]}
            rows={coverage.map((p) => ({
              ...p,
              perPerson: Math.round(p.perPerson * 100) / 100,
              familyCoverage: Math.round(p.familyCoverage * 1000) / 1000,
            }))}
          />
        </div>
        <div className="max-h-[28rem] overflow-auto">
          <DataTable
            columns={[
              { key: "province", label: "Province" },
              { key: "region", label: "Region" },
              { key: "affected", label: "People affected", numeric: true },
              { key: "value", label: "Relief value", numeric: true },
              { key: "perPerson", label: "PHP / person", numeric: true },
              { key: "familyCoverage", label: "Servings / family", numeric: true },
            ]}
            rows={coverage.map((p) => ({
              province: p.province,
              region: p.region,
              affected: full(p.affected),
              value: peso(p.value),
              perPerson: full(p.perPerson),
              familyCoverage: p.familyCoverage.toFixed(2),
            }))}
          />
        </div>
      </Card>
    </>
  );
}
