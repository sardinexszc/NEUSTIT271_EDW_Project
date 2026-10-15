const layers = [
  { schema: "raw", title: "Landing zone", text: "Five source systems landed exactly as received, with batch lineage." },
  { schema: "staging", title: "Cleanse & conform", text: "Data-quality rules standardize names, units and dates; bad rows are quarantined." },
  { schema: "dw", title: "Star schema", text: "Four fact tables sharing conformed dimensions: date, location (PSGC), event, organization." },
  { schema: "mart", title: "Data marts", text: "ROLAP aggregates for executive, operations and logistics dashboards." },
];

const facts = [
  { name: "Damage Assessment", type: "Transaction", grain: "event × city/municipality × damage category" },
  { name: "Evacuation Snapshot", type: "Periodic snapshot", grain: "evacuation center × day" },
  { name: "Resource Distribution", type: "Transaction", grain: "distribution line item" },
  { name: "Response Action", type: "Accumulating snapshot", grain: "response request (4 milestone dates)" },
];

const dashboards = ["Executive overview", "Evacuation operations", "Relief logistics"];

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 sm:py-16">
      <p className="text-sm font-medium tracking-wide text-sky-700 uppercase">IT271 Enterprise Data Warehousing</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
        Disaster Response Intelligence Warehouse
      </h1>
      <p className="mt-4 max-w-3xl text-lg text-slate-600">
        Integrating damage reports, evacuation-center occupancy, relief distribution and response logs for
        Philippine tropical cyclones and monsoon floods, 2020–2025, into one dimensional model for decision support.
      </p>
      <p className="mt-3 max-w-3xl rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
        Event names, dates and PSGC geography are real. All damage, evacuation, relief and response figures are synthetic.
      </p>

      <h2 className="mt-12 text-xl font-semibold text-slate-900">Architecture</h2>
      <ol className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {layers.map((l, i) => (
          <li key={l.schema} className="rounded-lg border border-slate-200 bg-white p-4">
            <span className="font-mono text-xs text-slate-500">{i + 1}. {l.schema}</span>
            <h3 className="mt-1 font-medium text-slate-900">{l.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{l.text}</p>
          </li>
        ))}
      </ol>

      <h2 className="mt-12 text-xl font-semibold text-slate-900">Fact tables</h2>
      <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-2 font-medium">Fact</th>
              <th className="px-4 py-2 font-medium">Type</th>
              <th className="px-4 py-2 font-medium">Grain (one row per…)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {facts.map((f) => (
              <tr key={f.name}>
                <td className="px-4 py-2 font-medium text-slate-900">{f.name}</td>
                <td className="px-4 py-2 text-slate-600">{f.type}</td>
                <td className="px-4 py-2 text-slate-600">{f.grain}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="mt-12 text-xl font-semibold text-slate-900">Dashboards</h2>
      <ul className="mt-4 grid gap-4 sm:grid-cols-3">
        {dashboards.map((d) => (
          <li key={d} className="rounded-lg border border-dashed border-slate-300 p-4 text-slate-500">
            {d}
            <span className="mt-1 block text-xs">In development</span>
          </li>
        ))}
      </ul>

      <footer className="mt-16 border-t border-slate-200 pt-6 text-sm text-slate-500">
        Ivan Christian Salinas · Aligned with the UNDRR Global Framework for Disaster-Related Statistics and the
        Sendai Framework 2015–2030.
      </footer>
    </main>
  );
}
