import type { Metadata } from "next";
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
      <LogisticsDashboard relief={relief} provinces={provinces} options={eventOptions} />
    </>
  );
}
