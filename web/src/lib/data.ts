// Data access for the dashboards. The marts are exported from the warehouse as a static
// JSON snapshot (ingestion/export_marts.py) because Vercel cannot reach the local
// PostgreSQL server. To go live on Supabase, replace these imports with queries against
// the mart schema; the types and every page stay the same.

import eventSummary from "@/data/mart_event_summary.json";
import impactCube from "@/data/mart_impact_cube.json";
import provinceImpact from "@/data/mart_province_event_impact.json";
import evacuationDaily from "@/data/mart_evacuation_daily.json";
import responsePerformance from "@/data/mart_response_performance.json";
import reliefByOrg from "@/data/mart_relief_by_org_category.json";
import displacementDaily from "@/data/mart_displacement_daily.json";
import lifelineRestoration from "@/data/mart_lifeline_restoration.json";
import exportMeta from "@/data/export_meta.json";

export type EventSummary = {
  event_code: string;
  event_name: string;
  local_name: string;
  international_name: string;
  hazard_type: string;
  category: string;
  category_rank: number | null;
  max_signal: number;
  start_date: string;
  end_date: string;
  event_year: number;
  dead: number;
  injured: number;
  missing: number;
  affected_families: number;
  affected_persons: number;
  houses_partially_damaged: number;
  houses_totally_damaged: number;
  damage_cost_php: number;
  housing_cost_php: number;
  infrastructure_cost_php: number;
  agriculture_cost_php: number;
  cities_municipalities_affected: number;
  provinces_affected: number;
  affected_area_population: number | null;
  dead_per_100k: number | null;
  missing_per_100k: number | null;
  affected_per_100k: number | null;
  dead_per_100k_national: number | null;
  peak_persons_in_centers: number | null;
  peak_families_in_centers: number | null;
  days_with_evacuees: number | null;
  centers_used: number | null;
  over_capacity_center_days: number | null;
  peak_persons_outside_centers: number | null;
  peak_persons_displaced: number | null;
  relief_value_php: number | null;
  relief_national_government_php: number | null;
  relief_lgu_php: number | null;
  relief_ngo_php: number | null;
  relief_international_php: number | null;
  families_served: number | null;
  distributions: number | null;
  relief_php_per_affected_person: number | null;
  response_requests: number | null;
  median_hours_to_dispatch: number | null;
  median_hours_to_arrive: number | null;
  completion_rate: number | null;
  lifeline_disruptions: number | null;
  lifelines_still_down: number | null;
  median_hours_to_restore: number | null;
};

export type ImpactCubeRow = {
  grouping_level: string;
  event_year: number | null;
  region_name: string | null;
  hazard_type: string | null;
  events: number;
  dead: number;
  affected_persons: number;
  houses_totally_damaged: number;
  damage_cost_php: number;
};

export type ProvinceImpact = {
  event_code: string;
  event_name: string;
  event_year: number;
  region_name: string;
  province_name: string;
  dead: number;
  affected_persons: number;
  affected_families: number;
  houses_totally_damaged: number;
  damage_cost_php: number;
  province_population: number | null;
  dead_per_100k: number | null;
  affected_per_100k: number | null;
  relief_value_php: number;
  families_served: number;
  relief_php_per_affected_person: number | null;
  family_coverage_ratio: number | null;
};

export type EvacuationDay = {
  event_code: string;
  snapshot_date: string;
  day_of_event: number;
  centers_open: number;
  families_inside: number;
  persons_inside: number;
  capacity_families: number;
  centers_over_capacity: number;
  occupancy_rate: number;
};

export type ResponsePerformance = {
  event_code: string;
  response_type: string;
  priority: string;
  requests: number;
  median_hours_to_dispatch: number;
  p90_hours_to_dispatch: number;
  median_hours_to_arrive: number;
  median_hours_to_complete: number | null;
  completion_rate: number;
  personnel_deployed: number;
};

export type ReliefByOrg = {
  event_code: string;
  org_code: string;
  org_name: string;
  org_type: string;
  resource_category: string;
  distributions: number;
  line_items: number;
  relief_value_php: number;
  families_served: number;
};

export type DisplacementDay = {
  event_code: string;
  snapshot_date: string;
  day_of_event: number;
  families_inside: number;
  persons_inside: number;
  families_outside: number;
  persons_outside: number;
  persons_displaced: number;
  share_outside_centers: number | null;
};

export type LifelineRestoration = {
  event_code: string;
  lifeline_code: string;
  lifeline_name: string;
  lifeline_sector: string;
  unit_of_measure: string;
  places_disrupted: number;
  units_affected: number;
  places_restored: number;
  places_still_down: number;
  restored_within_72h: number;
  share_restored_within_72h: number;
  median_hours_to_restore: number | null;
  p90_hours_to_restore: number | null;
};

export const events = (eventSummary as EventSummary[]).sort((a, b) => a.start_date.localeCompare(b.start_date));
export const cube = impactCube as ImpactCubeRow[];
export const provinces = provinceImpact as ProvinceImpact[];
export const evacuation = evacuationDaily as EvacuationDay[];
export const response = responsePerformance as ResponsePerformance[];
export const relief = reliefByOrg as ReliefByOrg[];
export const displacement = displacementDaily as DisplacementDay[];
export const lifelines = lifelineRestoration as LifelineRestoration[];
export const exportedAt: string = exportMeta.exported_at;

/** The event options every dashboard filter offers, newest first. */
export const eventOptions = [...events]
  .reverse()
  .map((e) => ({ code: e.event_code, label: `${e.event_name} · ${e.event_year}` }));
