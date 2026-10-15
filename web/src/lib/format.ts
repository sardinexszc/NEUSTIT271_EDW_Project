const compact = new Intl.NumberFormat("en-PH", { notation: "compact", maximumFractionDigits: 1 });
const whole = new Intl.NumberFormat("en-PH", { maximumFractionDigits: 0 });

/** 54_100_000_000 -> "₱54.1B" */
export function peso(value: number | null | undefined): string {
  if (value == null) return "–";
  return "₱" + compact.format(value);
}

/** 1_234_567 -> "1.2M" */
export function count(value: number | null | undefined): string {
  if (value == null) return "–";
  return compact.format(value);
}

/** 1234567 -> "1,234,567" (tables) */
export function full(value: number | null | undefined): string {
  if (value == null) return "–";
  return whole.format(value);
}

export function hours(value: number | null | undefined): string {
  if (value == null) return "–";
  return value < 1 ? `${Math.round(value * 60)} min` : `${value.toFixed(1)} h`;
}

export function percent(value: number | null | undefined, digits = 1): string {
  if (value == null) return "–";
  return `${(value * 100).toFixed(digits)}%`;
}

export function shortDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-PH", { month: "short", day: "numeric" });
}
