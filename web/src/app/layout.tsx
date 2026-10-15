import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";
import { exportedAt } from "@/lib/data";

export const metadata: Metadata = {
  title: "DRIW | Disaster Response Intelligence Warehouse",
  description:
    "IT271 Enterprise Data Warehousing project: disaster-response analytics for the Philippines, 2020-2025.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <div className="border-b border-[var(--border)] bg-surface">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-semibold">DRIW</p>
              <p className="text-xs text-ink-2">Disaster Response Intelligence Warehouse · Philippines 2020–2025</p>
            </div>
            <Nav />
          </div>
        </div>
        <div className="bg-[var(--notice-bg)] text-[var(--notice-ink)]">
          <p className="mx-auto max-w-6xl px-4 py-2 text-sm">
            Event names, dates and PSGC geography are real. All damage, evacuation, relief and response figures are
            synthetic, generated for demonstration.
          </p>
        </div>
        <main className="mx-auto max-w-6xl px-4 py-6 sm:py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 pb-8 text-xs text-muted">
          IT271 Enterprise Data Warehousing · Ivan Christian Salinas · Data snapshot exported{" "}
          {new Date(exportedAt).toLocaleString("en-PH", { dateStyle: "medium", timeStyle: "short" })}
        </footer>
      </body>
    </html>
  );
}
