import type { Metadata } from "next";
import { Suspense } from "react";
import { PageHeader } from "@/components/ui";
import { displacement, evacuation, eventOptions, events, lifelines, response } from "@/lib/data";
import { OperationsDashboard } from "./operations-dashboard";

export const metadata: Metadata = { title: "Operations | DRIW" };

export default function OperationsPage() {
  // default to the event with the largest evacuation
  const initial = [...events].sort((a, b) => (b.peak_persons_in_centers ?? 0) - (a.peak_persons_in_centers ?? 0))[0];
  return (
    <>
      <PageHeader
        title="Operations"
        description="Displacement, evacuation-center load, lifeline restoration and emergency response timeliness for a single event."
      />
      {/* the selected event is read from the URL, which needs a Suspense boundary on a static page */}
      <Suspense fallback={<p className="text-ink-2">Loading dashboard…</p>}>
        <OperationsDashboard
          events={events}
          evacuation={evacuation}
          displacement={displacement}
          lifelines={lifelines}
          response={response.filter((r) => r.event_code !== "All")}
          options={eventOptions}
          initial={initial.event_code}
        />
      </Suspense>
    </>
  );
}
