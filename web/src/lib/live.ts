"use client";

import { useEffect, useState } from "react";

/**
 * Base URL of the PHP API (e.g. "/driw/api"), set only for XAMPP builds. Elsewhere (dev server,
 * Vercel) it is empty and the dashboards use the bundled snapshot without trying the network.
 */
export const API_BASE = process.env.NEXT_PUBLIC_DRIW_API ?? "";

export type Source = "snapshot" | "live";

/**
 * Rows of one data mart: the bundled snapshot first (instant render), then live rows from the
 * PostgreSQL warehouse through the PHP API. If the API or database is down, the snapshot stays.
 */
export function useMart<T>(name: string, snapshot: T[]): { rows: T[]; source: Source } {
  const [state, setState] = useState<{ rows: T[]; source: Source }>({ rows: snapshot, source: "snapshot" });

  useEffect(() => {
    if (!API_BASE) return;
    const controller = new AbortController();
    fetch(`${API_BASE}/marts.php?name=${encodeURIComponent(name)}`, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((rows: T[]) => {
        if (Array.isArray(rows)) setState({ rows, source: "live" });
      })
      .catch(() => {
        /* keep the snapshot */
      });
    return () => controller.abort();
  }, [name]);

  return state;
}

export type Health = { status: "ok"; database: string; role: string; postgres: string; checked_at: string };

/** Warehouse connection status for the footer badge; null while unknown or without an API. */
export function useHealth(): Health | "offline" | null {
  const [health, setHealth] = useState<Health | "offline" | null>(null);
  useEffect(() => {
    if (!API_BASE) return;
    fetch(`${API_BASE}/health.php`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((h: Health) => setHealth(h))
      .catch(() => setHealth("offline"));
  }, []);
  return health;
}
