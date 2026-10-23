import type { Metadata } from "next";
import { Card, DataTable, PageHeader } from "@/components/ui";

export const metadata: Metadata = { title: "About the warehouse | DRIW" };

const layers = [
  { schema: "raw", title: "Landing zone", text: "Five source systems (CSV, Excel, JSON) landed exactly as received, with batch lineage." },
  { schema: "staging", title: "Cleanse & conform", text: "45 data-quality rules standardize names, units and dates; failing rows are quarantined." },
  { schema: "dw", title: "Star schema", text: "Six fact tables sharing ten conformed dimensions, with SCD Type 2 locations." },
  { schema: "mart", title: "Data marts", text: "Materialized views and GROUP BY CUBE / GROUPING SETS aggregates for these dashboards." },
];

const facts = [
  { fact: "Damage assessment", type: "Transaction", grain: "event × city/municipality × damage category" },
  { fact: "Evacuation snapshot", type: "Periodic snapshot", grain: "evacuation center × day × event" },
  { fact: "Resource distribution", type: "Transaction", grain: "relief distribution line item" },
  { fact: "Response action", type: "Accumulating snapshot", grain: "response request (4 milestone dates)" },
  { fact: "Displacement outside centers", type: "Periodic snapshot", grain: "city/municipality × day × event" },
  { fact: "Lifeline disruption", type: "Accumulating snapshot", grain: "event × city/municipality × lifeline" },
];

const sources = [
  { source: "NDRRMC situation reports", format: "CSV", defects: "Duplicates, missing values, thousands separators, negative costs" },
  { source: "DSWD DROMIC evacuation", format: "Excel", defects: "Mixed date formats, missing center codes, overcrowding" },
  { source: "NGO relief distribution", format: "Nested JSON", defects: "Organization aliases, partner item codes and units, missing locations" },
  { source: "PAGASA bulletins", format: "CSV", defects: "Re-issued (duplicate) bulletins" },
  { source: "LGU response logs", format: "CSV", defects: "Non-standard request types, arrival before dispatch" },
];

export default function AboutPage() {
  return (
    <>
      <PageHeader
        title="About the warehouse"
        description="How fragmented disaster-response data becomes one dimensional model for decision support."
      />

      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {layers.map((l, i) => (
          <li key={l.schema} className="rounded-xl border border-[var(--border)] bg-surface p-4">
            <span className="font-mono text-xs text-muted">
              {i + 1}. {l.schema}
            </span>
            <h2 className="mt-1 font-semibold">{l.title}</h2>
            <p className="mt-1 text-sm text-ink-2">{l.text}</p>
          </li>
        ))}
      </ol>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Fact tables">
          <div className="overflow-x-auto">
            <DataTable
              columns={[
                { key: "fact", label: "Fact" },
                { key: "type", label: "Type" },
                { key: "grain", label: "Grain (one row per…)" },
              ]}
              rows={facts}
            />
          </div>
        </Card>
        <Card title="Simulated source systems" subtitle="Each with deliberately planted, counted defects">
          <div className="overflow-x-auto">
            <DataTable
              columns={[
                { key: "source", label: "Source" },
                { key: "format", label: "Format" },
                { key: "defects", label: "Typical defects" },
              ]}
              rows={sources}
            />
          </div>
        </Card>
      </div>

      <Card title="Data quality, proven" className="mt-4">
        <p className="text-sm text-ink-2">
          The generator records every defect it plants. The data-quality layer detects all 19 defect types at exactly the
          planted counts, and place-name matching against the PSGC was checked against ground truth with zero false
          matches. Rejected rows are held in a quarantine table with their reasons; they never reach these dashboards.
        </p>
      </Card>

      <p className="mt-6 text-sm text-ink-2">
        Built with PostgreSQL 17, Python, dbt and Next.js. Aligned with the UNDRR Global Framework for Disaster-Related
        Statistics and the Sendai Framework for Disaster Risk Reduction 2015–2030.
      </p>
    </>
  );
}
