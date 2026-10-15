import type { Metadata } from "next";
import { Suspense } from "react";
import { PageHeader } from "@/components/ui";
import { eventOptions, provinces, relief } from "@/lib/data";
import { LogisticsDashboard } from "./logistics-dashboard";

export const metadata: Metadata = { title: "Logistics | DRIW" };

export default function LogisticsPage() {
  return (
    <>
      <PageHeader
        title="Logistics"
        description="Relief delivered by organization and resource type, and how well it matched the impact in each province."
      />
      {/* the selected event is read from the URL, which needs a Suspense boundary on a static page */}
      <Suspense fallback={<p className="text-ink-2">Loading dashboard…</p>}>
        <LogisticsDashboard relief={relief} provinces={provinces} options={eventOptions} />
      </Suspense>
    </>
  );
}
