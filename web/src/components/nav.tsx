"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Executive" },
  { href: "/operations", label: "Operations" },
  { href: "/logistics", label: "Logistics" },
  { href: "/about", label: "About" },
];

export function Nav() {
  const path = usePathname();
  return (
    <nav aria-label="Dashboards" className="-mx-1 flex gap-1 overflow-x-auto">
      {links.map((l) => {
        const active = l.href === "/" ? path === "/" : path.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm ${
              active ? "bg-[var(--grid)] font-medium text-ink" : "text-ink-2 hover:text-ink"
            }`}
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}
