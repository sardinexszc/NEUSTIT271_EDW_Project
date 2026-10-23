import type { Metadata } from "next";
import "./globals.css";
import { DataSource } from "@/components/data-source";
import { Nav } from "@/components/nav";
import { exportedAt } from "@/lib/data";

const DESCRIPTION =
  "IT271 Enterprise Data Warehousing project: disaster-response analytics for the Philippines, 2020–2025.";

// Link previews need absolute URLs: the XAMPP folder, Vercel's production domain, or the dev server.
const siteUrl =
  process.env.DRIW_TARGET === "xampp"
    ? `http://localhost${process.env.DRIW_BASE_PATH ?? "/driw"}/`
    : process.env.VERCEL_PROJECT_PRODUCTION_URL
      ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
      : "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "DRIW | Disaster Response Intelligence Warehouse",
  description: DESCRIPTION,
  openGraph: {
    title: "Disaster Response Intelligence Warehouse",
    description: DESCRIPTION,
    siteName: "DRIW",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Disaster Response Intelligence Warehouse",
    description: DESCRIPTION,
  },
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
          IT271 Enterprise Data Warehousing · Ivan Christian Salinas · <DataSource exportedAt={exportedAt} />
        </footer>
      </body>
    </html>
  );
}
