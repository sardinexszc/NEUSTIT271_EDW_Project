"use client";

import { API_BASE, useHealth } from "@/lib/live";

/** Footer line saying where the numbers come from: the live warehouse or the bundled snapshot. */
export function DataSource({ exportedAt }: { exportedAt: string }) {
  const health = useHealth();
  const snapshot = `Data snapshot exported ${new Date(exportedAt).toLocaleString("en-PH", {
    dateStyle: "medium",
    timeStyle: "short",
  })}`;

  if (!API_BASE || health === null) return <span>{snapshot}</span>;
  if (health === "offline") return <span>{snapshot} · warehouse offline, showing the snapshot</span>;
  return (
    <span>
      Live from the PostgreSQL {health.postgres} warehouse “{health.database}” as read-only role {health.role}
    </span>
  );
}
