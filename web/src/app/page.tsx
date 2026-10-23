import { cube, events } from "@/lib/data";
import { ExecutiveDashboard } from "./executive-dashboard";

export default function ExecutivePage() {
  return <ExecutiveDashboard eventsSnapshot={events} cubeSnapshot={cube} />;
}
