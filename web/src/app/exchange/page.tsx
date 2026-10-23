import type { Metadata } from "next";
import { Card, PageHeader } from "@/components/ui";
import catalog from "@/data/intake_catalog.json";
import { eventOptions } from "@/lib/data";
import { ExchangeForm, ExcelExport, TemplateLink } from "./exchange-client";

export const metadata: Metadata = { title: "Data exchange | DRIW" };

export default function ExchangePage() {
  return (
    <>
      <PageHeader
        title="Data exchange"
        description="For LGUs and national DRRM offices: download a template, check and submit a report, and download the warehouse's data as Excel."
      />

      <Card title="1. Download a template" subtitle="One Excel workbook per report type, with instructions and drop-down lists of official names">
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {catalog.report_types.map((t) => (
            <li key={t.key} className="flex flex-col gap-1 rounded-lg border border-[var(--border)] p-4">
              <p className="font-medium">{t.title}</p>
              <p className="text-sm text-ink-2">{t.issuer}</p>
              <p className="text-sm text-ink-2">{t.description}</p>
              <p className="text-xs text-muted">
                {t.columns.length} columns, {t.columns.filter((c) => c.required).length} required
              </p>
              <TemplateLink href={t.template} />
            </li>
          ))}
        </ul>
      </Card>

      <div className="mt-4">
        <ExchangeForm reportTypes={catalog.report_types} profiles={catalog.profiles} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="3. Download data as Excel" subtitle="The data marts, live from the warehouse: one sheet per table, plus a data dictionary">
          <ExcelExport options={eventOptions} />
        </Card>

        <Card title="Supported layouts" subtitle="An LGU's own column headings, mapped once to the standard layout">
          <ul className="flex flex-col gap-3 text-sm">
            <li>
              <p className="font-medium">DRIW template</p>
              <p className="text-ink-2">The downloadable templates above, for every report type.</p>
            </li>
            {catalog.profiles.map((p) => (
              <li key={p.id}>
                <p className="font-medium">{p.name}</p>
                <p className="text-ink-2">{p.description}</p>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">
            A new layout is a small file in <code>ingestion/intake_profiles/</code> that lists the office&apos;s
            headings and the standard column each one means.
          </p>
        </Card>
      </div>

      <Card title="How each row is checked" subtitle="Submission rules first, then the warehouse's own data-quality rules" className="mt-4">
        <ul className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          {Object.entries(catalog.submission_rules).map(([code, text]) => (
            <li key={code}>
              <span className="font-mono text-xs text-muted">{code}</span>
              <p className="text-ink-2">{text}</p>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm text-ink-2">
          Every row then goes through the same data-quality rules as the warehouse: place names are matched to the
          official PSGC, events and organizations to their master lists, units converted, and impossible values
          rejected with the reason.
        </p>
      </Card>
    </>
  );
}
