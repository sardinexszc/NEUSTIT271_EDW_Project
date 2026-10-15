"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

/**
 * The selected event, kept in the URL (`?event=TC2024-KRISTINE`) so a view can be
 * bookmarked, shared or reloaded. Unknown or missing values fall back to `fallback`,
 * which is left out of the URL to keep default links clean.
 */
export function useEventParam(validCodes: string[], fallback: string) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const requested = params.get("event")?.toUpperCase();
  const code = requested && validCodes.includes(requested) ? requested : fallback;

  function setCode(next: string) {
    const query = new URLSearchParams(params.toString());
    if (next === fallback) query.delete("event");
    else query.set("event", next);
    const qs = query.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }

  return [code, setCode] as const;
}
