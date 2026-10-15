import type { Metadata } from "next";
import { PageHeader } from "@/components/ui";
import { evacuation, eventOptions, events, response } from "@/lib/data";
import { OperationsDashboard } from "./operations-dashboard";

export const metadata: Metadata = { title: "Operations | DRIW" };

export default function OperationsPage() {
  // default to the event with the largest evacuation
  const initial = [...events].sort((a, b) => (b.peak_persons_in_centers ?? 0) - (a.peak_persons_in_centers ?? 0))[0];
  return (
    <>
      <PageHeader
        title="Operations"
        description="Evacuation-center load and emergency response timeliness for a single event."
      />
      <OperationsDashboard
        events={events}
        evacuation={evacuation}
        response={response.filter((r) => r.event_code !== "All")}
        options={eventOptions}
        initial={initial.event_code}
      />
    </>
  );
}
