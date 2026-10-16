import { ImageResponse } from "next/og";
import { events } from "@/lib/data";

// Link preview for chat apps and social sites, rendered once at build time.
export const alt = "DRIW: Disaster Response Intelligence Warehouse, Philippines 2020–2025";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const dynamic = "force-static"; // required for the XAMPP static export

export default function OpengraphImage() {
  const damage = events.reduce((t, e) => t + e.damage_cost_php, 0);
  const affected = events.reduce((t, e) => t + e.affected_persons, 0);
  const stats = [
    // "PHP", not "₱": the image renderer's built-in font has no peso sign
    { value: `PHP ${(damage / 1e9).toFixed(1)}B`, label: "damage" },
    { value: `${(affected / 1e6).toFixed(1)}M`, label: "people affected" },
    { value: String(events.length), label: "events" },
  ];

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between",
          padding: 72, background: "#14233A", color: "#F6F4EF", fontFamily: "sans-serif", position: "relative",
        }}
      >
        <div style={{ position: "absolute", right: -120, top: 60, width: 520, height: 520, borderRadius: 520,
          border: "3px solid #2C4466", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: 340, height: 340, borderRadius: 340, border: "3px solid #3E5F8C",
            display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 70, height: 70, borderRadius: 70, background: "#E0612A" }} />
          </div>
        </div>
        <div style={{ fontSize: 26, letterSpacing: 2, textTransform: "uppercase", color: "#F08A5D" }}>
          IT271 Enterprise Data Warehousing
        </div>
        <div style={{ display: "flex", flexDirection: "column", maxWidth: 820 }}>
          <div style={{ fontSize: 68, fontWeight: 700, lineHeight: 1.05 }}>Disaster Response Intelligence Warehouse</div>
          <div style={{ fontSize: 30, marginTop: 20, color: "#C9D3DE" }}>Philippines, 2020–2025 · synthetic operational figures</div>
        </div>
        <div style={{ display: "flex", gap: 56 }}>
          {stats.map((s) => (
            <div key={s.label} style={{ display: "flex", flexDirection: "column" }}>
              <div style={{ fontSize: 44, fontWeight: 700 }}>{s.value}</div>
              <div style={{ fontSize: 24, color: "#C9D3DE" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
