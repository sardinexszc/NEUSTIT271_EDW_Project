"""Generate SYNTHETIC source-system extracts for the DRIW warehouse.

Real:       event names/dates (data/reference/events.csv), PSGC geography and population.
Synthetic:  every damage, evacuation, distribution and response figure.

Five simulated source systems are written to data/sources/, each in its own format and
each with its own realistic defects (spelling variants, duplicates, mixed date formats,
unit mismatches, impossible values...). Every planted defect is counted in
data/sources/_defect_manifest.json so the data-quality layer can be reconciled against it.

Output is fully deterministic for a given --seed.
"""

import argparse
import csv
import itertools
import json
import math
import random
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from openpyxl import Workbook

from common import REFERENCE_DIR, SOURCES_DIR

PERSONS_PER_FAMILY = (4.0, 4.8)
DAMAGE_CATEGORIES = ["Population", "Housing", "Infrastructure", "Agriculture"]
CATEGORY_WIND_KPH = {
    "Tropical Depression": 55, "Tropical Storm": 85, "Severe Tropical Storm": 110,
    "Typhoon": 150, "Super Typhoon": 195,
}
NGO_ORG_NAMES = {  # canonical org -> names its field staff actually type
    "PRC": ["Philippine Red Cross", "PRC", "Red Cross PH", "Phil Red Cross"],
    "CARITAS": ["Caritas Philippines", "Caritas", "Caritas PH"],
    "WFP": ["WFP", "World Food Programme", "UN WFP"],
    "UNICEF": ["UNICEF", "UNICEF PH"],
    "DSWD": ["DSWD", "DSWD-FO"],
}
NGO_ITEMS = {  # item -> source codes/units used by partners (see resource_items.csv aliases)
    "FFP": [("FFP", "pack", 1), ("FOODPACK", "pack", 1), ("FP-01", "box", 1)],
    "RICE": [("RICE", "kg", 1), ("RICE-SACK", "sack", 50), ("R50", "sack", 50)],
    "WATER": [("WATER", "liter", 1), ("H2O-CASE", "case", 6), ("BW500", "bottle", 0.5)],
    "HYGKIT": [("HYGKIT", "kit", 1), ("HK-STD", "kit", 1)],
    "SLPKIT": [("SLPKIT", "kit", 1), ("SK-01", "kit", 1)],
    "KITCHEN": [("KITCHEN", "kit", 1), ("KK-01", "set", 1)],
    "TARP": [("TARP", "piece", 1), ("TP-4x6", "roll", 10)],
    "SHELTERKIT": [("SHELTERKIT", "kit", 1), ("ESK", "kit", 1)],
    "MEDKIT": [("MEDKIT", "kit", 1), ("MED-BOX", "box", 1)],
    "WATERKIT": [("WATERKIT", "kit", 1), ("WPK", "kit", 1)],
}
REQUEST_TYPES = {  # code -> (typical responding units, base hours to dispatch, on-site hours)
    "RESCUE": (["MDRRMO Rescue Team", "BFP", "PCG", "AFP"], 0.5, 4),
    "MEDEVAC": (["DOH-HEMS", "MDRRMO Rescue Team", "AFP"], 0.7, 3),
    "EVAC_ASSIST": (["MDRRMO Rescue Team", "AFP", "PNP"], 1.5, 6),
    "ROAD_CLEAR": (["DPWH", "AFP", "MDRRMO Rescue Team"], 6, 18),
    "RELIEF_DELIV": (["DSWD", "MDRRMO Rescue Team", "AFP"], 8, 10),
}


# --------------------------------------------------------------------------- helpers

class Defects:
    """Counts every defect planted, per source and type."""

    def __init__(self) -> None:
        self.counts: Counter = Counter()

    def hit(self, rng: random.Random, rate: float, source: str, kind: str) -> bool:
        if rng.random() < rate:
            self.counts[f"{source}.{kind}"] += 1
            return True
        return False


def read_csv(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def name_variant(rng: random.Random, name: str) -> str:
    """A plausible way a human might type an official PSGC name."""
    options = [name.upper(), name.lower(), f" {name} ", name.replace("ñ", "n").replace("Ñ", "N")]
    if name.startswith("City of "):
        base = name[len("City of "):]
        options += [f"{base} City", base, f"{base.upper()} CITY"]
    if "Santo " in name or "Santa " in name:
        options += [name.replace("Santo ", "Sto. ").replace("Santa ", "Sta. ")]
    if len(name) > 5:  # one transposed letter
        i = rng.randrange(1, len(name) - 2)
        options.append(name[:i] + name[i + 1] + name[i] + name[i + 2:])
    options = [o for o in options if o != name]
    return rng.choice(options) if options else f" {name} "


def fmt_date(rng: random.Random, d: date, style: str) -> str | float:
    if style == "iso":
        return d.isoformat()
    if style == "us":
        return d.strftime("%m/%d/%Y")
    if style == "dmy":
        return d.strftime("%d-%b-%Y")
    if style == "excel":  # Excel serial number, as when a cell loses its date format
        return float((d - date(1899, 12, 30)).days)
    raise ValueError(style)


MISSING_TOKENS = ("", "N/A", "-", "TBD")
NDRRMC_REQUIRED = {
    "Population": ["dead", "injured", "missing", "affected_families", "affected_persons"],
    "Housing": ["houses_partial", "houses_total", "cost_php"],
    "Infrastructure": ["cost_php"],
    "Agriculture": ["cost_php"],
}


def fmt_number(rng: random.Random, n: float) -> str:
    if rng.random() < 0.01:
        return rng.choice(MISSING_TOKENS)
    if rng.random() < 0.03 and n >= 1000:
        return f"{n:,.0f}"
    return f"{n:.0f}"


def count_ndrrmc_defects(defects: Defects, r: dict, official_name: str) -> None:
    """Count defects by inspecting the finished row, so duplicated rows are counted too."""
    c = defects.counts
    if r["city_muni"] != official_name:
        c["ndrrmc.location_name_variant"] += 1
    for field in NDRRMC_REQUIRED[r["damage_category"]]:
        if r[field] in MISSING_TOKENS:
            c["ndrrmc.missing_value"] += 1
        elif "," in r[field]:
            c["ndrrmc.thousands_separator"] += 1
    if r["cost_php"] not in MISSING_TOKENS and r["cost_php"].startswith("-"):
        c["ndrrmc.negative_value"] += 1
    fam, per = r["affected_families"], r["affected_persons"]
    if r["damage_category"] == "Population" and fam not in MISSING_TOKENS and per not in MISSING_TOKENS:
        if float(per.replace(",", "")) < float(fam.replace(",", "")):
            c["ndrrmc.persons_less_than_families"] += 1


# --------------------------------------------------------------------------- geography

def load_geography():
    citymun = read_csv(REFERENCE_DIR / "psgc_citymun.csv")
    barangays = read_csv(REFERENCE_DIR / "psgc_barangay.csv")
    by_province = defaultdict(list)
    for c in citymun:
        c["population"] = int(c["population"] or 0) or 25_000
        by_province[c["province_name"].lower()].append(c)
    brgy_by_citymun = defaultdict(list)
    for b in barangays:
        brgy_by_citymun[b["city_muni_code"]].append(b["name"])
    return by_province, brgy_by_citymun


def evacuation_centers(citymun: dict, barangays: list[str]) -> list[dict]:
    """Stable registry of evacuation centers per city/municipality (reused across events)."""
    rng = random.Random(f"ec-{citymun['psgc_code']}")
    count = 3 + citymun["population"] // 40_000
    centers = []
    for n in range(min(count, 14)):
        brgy = rng.choice(barangays) if barangays else citymun["name"]
        kind, label = rng.choice([
            ("School", f"{brgy} Elementary School"),
            ("School", f"{brgy} National High School"),
            ("Covered Court", f"{brgy} Covered Court"),
            ("Barangay Hall", f"Brgy. {brgy} Hall"),
            ("Gymnasium", f"{citymun['name']} Gymnasium"),
            ("Church", f"{brgy} Parish Church"),
        ])
        centers.append({
            "code": f"EC-{citymun['psgc_code'][:7]}-{n + 1:03d}",
            "name": label, "type": kind, "barangay": brgy,
            "capacity": rng.choice([40, 60, 80, 120, 150, 200, 300, 400]),
        })
    return centers


# --------------------------------------------------------------------------- generator

def impacted_areas(rng, event, by_province):
    """Pick affected cities/municipalities; the first listed province is hit hardest."""
    areas = []
    for rank, prov in enumerate(event["affected_provinces"].split(";")):
        munis = by_province.get(prov.lower())
        if not munis:
            raise SystemExit(f"{event['event_code']}: province '{prov}' not found in PSGC")
        prov_weight = 0.85 ** rank
        share = min(1.0, 0.3 + 0.5 * float(event["severity_weight"]) * prov_weight)
        for m in rng.sample(munis, max(1, round(len(munis) * share))):
            impact = float(event["severity_weight"]) * prov_weight * rng.uniform(0.25, 1.0)
            areas.append((m, impact))
    return areas


def generate(seed: int) -> None:
    rng = random.Random(seed)
    defects = Defects()
    by_province, brgy_by_citymun = load_geography()
    events = read_csv(REFERENCE_DIR / "events.csv")

    for sub in ["ndrrmc", "dromic", "ngo", "pagasa", "lgu"]:
        (SOURCES_DIR / sub).mkdir(parents=True, exist_ok=True)

    pagasa_rows, ngo_by_year, lgu_rows = [], defaultdict(list), []
    totals = Counter()
    seq = itertools.count(1)  # unique source IDs

    for event in events:
        start = date.fromisoformat(event["start_date"])
        end = date.fromisoformat(event["end_date"])
        areas = impacted_areas(rng, event, by_province)
        incident = f"{event['category']} {event['local_name']} ({event['international_name']})"

        # ---- PAGASA bulletin (one row per event, sometimes re-issued = duplicate)
        row = {
            "local_name": event["local_name"].upper(),
            "international_name": event["international_name"].upper(),
            "category": event["category"],
            "max_wind_kph": CATEGORY_WIND_KPH.get(event["category"], ""),
            "max_signal": event["max_signal"],
            "start_date": start.strftime("%b %d, %Y"),
            "end_date": end.strftime("%b %d, %Y"),
            "affected_areas": event["affected_provinces"].replace(";", ", "),
        }
        pagasa_rows.append(row)
        if defects.hit(rng, 0.25, "pagasa", "duplicate_bulletin"):
            pagasa_rows.append(dict(row))

        # ---- NDRRMC sitreps: cumulative figures, more areas reported each sitrep
        sitreps = rng.randint(2, 4)
        ndrrmc_rows = []
        for area, impact in areas:
            pop = area["population"]
            persons = pop * impact * rng.uniform(0.05, 0.35)
            families = persons / rng.uniform(*PERSONS_PER_FAMILY)
            final = {
                "dead": max(0, round(rng.expovariate(1) * persons * 2e-4 * impact)),
                "injured": max(0, round(rng.expovariate(1) * persons * 8e-4 * impact)),
                "missing": max(0, round(rng.expovariate(1.5) * persons * 1e-4 * impact)),
                "families": families, "persons": persons,
                "partial": families * impact * rng.uniform(0.05, 0.25),
                "total": families * impact * rng.uniform(0.005, 0.06),
                "infra": pop * impact * rng.uniform(80, 900),
                "agri": pop * impact * rng.uniform(50, 1500),
            }
            first_reported = rng.randint(1, sitreps)
            for s in range(first_reported, sitreps + 1):
                frac = 0.4 + 0.6 * s / sitreps
                v = {k: val * frac for k, val in final.items()}
                rdate = end + timedelta(days=s - 1)
                prov = area["province_name"]
                muni = area["name"]
                if rng.random() < 0.06:
                    muni = name_variant(rng, muni)
                for cat in DAMAGE_CATEGORIES:
                    r = {
                        "sitrep_no": f"SitRep No. {s}", "report_date": rdate.isoformat(),
                        "incident_name": incident, "region": area["region_name"],
                        "province": prov, "city_muni": muni, "damage_category": cat,
                        "dead": "", "injured": "", "missing": "", "affected_families": "",
                        "affected_persons": "", "houses_partial": "", "houses_total": "",
                        "cost_php": "", "remarks": "",
                    }
                    if cat == "Population":
                        r.update(dead=fmt_number(rng, v["dead"]),
                                 injured=fmt_number(rng, v["injured"]),
                                 missing=fmt_number(rng, v["missing"]),
                                 affected_families=fmt_number(rng, v["families"]),
                                 affected_persons=fmt_number(rng, v["persons"]))
                        if rng.random() < 0.004:  # families/persons swapped
                            r["affected_persons"], r["affected_families"] = r["affected_families"], r["affected_persons"]
                    elif cat == "Housing":
                        r.update(houses_partial=fmt_number(rng, v["partial"]),
                                 houses_total=fmt_number(rng, v["total"]),
                                 cost_php=fmt_number(rng, v["partial"] * 15_000 + v["total"] * 120_000))
                    else:
                        cost = v["infra"] if cat == "Infrastructure" else v["agri"]
                        if rng.random() < 0.003:  # sign error
                            cost = -cost
                        r["cost_php"] = fmt_number(rng, cost)
                    if s < sitreps and rng.random() < 0.1:
                        r["remarks"] = "Validation ongoing"
                    ndrrmc_rows.append(r)
                    count_ndrrmc_defects(defects, r, area["name"])
                    if defects.hit(rng, 0.015, "ndrrmc", "duplicate_row"):
                        ndrrmc_rows.append(dict(r))
                        count_ndrrmc_defects(defects, r, area["name"])
            totals["damage_assessment_final_rows"] += len(DAMAGE_CATEGORIES)
        write_csv(SOURCES_DIR / "ndrrmc" / f"sitreps_{event['event_code']}.csv", ndrrmc_rows)

        # ---- DSWD DROMIC: daily evacuation-center occupancy, one workbook per event
        office_style = rng.choice(["iso", "us", "dmy", "excel"])  # each field office has its habits
        wb = Workbook()
        ws = wb.active
        ws.title = "Inside ECs"
        ws.append(["Report Date", "Disaster", "Region", "Province", "City/Municipality", "Barangay",
                   "EC Code", "Evacuation Center", "EC Type", "Capacity (Families)",
                   "Families Inside", "Persons Inside"])
        for area, impact in areas:
            if impact < 0.3:
                continue
            centers = evacuation_centers(area, brgy_by_citymun.get(area["psgc_code"], []))
            used = centers[: max(1, round(len(centers) * min(1.0, impact * 1.2)))]
            stay_days = 2 + round(impact * 10)
            for ec in used:
                peak = ec["capacity"] * rng.uniform(0.4, 1.0) * min(1.3, 0.6 + impact)
                for d in range(-1, (end - start).days + stay_days):
                    day = start + timedelta(days=d)
                    t = max(0, d)
                    fam = peak * (0.5 if d < 0 else 1.0) * math.exp(-t / max(1.5, stay_days / 2.2))
                    fam = round(fam * rng.uniform(0.85, 1.1))
                    if fam <= 0:
                        break
                    persons = round(fam * rng.uniform(*PERSONS_PER_FAMILY))
                    if fam > ec["capacity"]:
                        defects.counts["dromic.over_capacity"] += 1
                    style = office_style
                    if defects.hit(rng, 0.05, "dromic", "inconsistent_date_format"):
                        style = rng.choice([f for f in ("iso", "us", "dmy", "excel") if f != office_style])
                    code = ec["code"]
                    if defects.hit(rng, 0.02, "dromic", "missing_ec_code"):
                        code = None
                    muni = area["name"]
                    if defects.hit(rng, 0.05, "dromic", "location_name_variant"):
                        muni = name_variant(rng, muni)
                    if defects.hit(rng, 0.003, "dromic", "persons_less_than_families"):
                        persons = max(0, fam - rng.randint(1, 5))
                    ws.append([fmt_date(rng, day, style), event["local_name"], area["region_name"],
                               area["province_name"], muni, ec["barangay"], code, ec["name"],
                               ec["type"], ec["capacity"], fam, persons])
                    totals["evacuation_snapshot_rows"] += 1
        wb.save(SOURCES_DIR / "dromic" / f"dromic_{event['event_code']}.xlsx")

        # ---- NGO / agency relief distribution (nested JSON, one file per year)
        for area, impact in areas:
            for _ in range(rng.randint(1, 2 + round(impact * 6))):
                org = rng.choice(list(NGO_ORG_NAMES))
                day = start + timedelta(days=rng.randint(0, 21))
                lines = []
                for item in rng.sample(list(NGO_ITEMS), rng.randint(1, 4)):
                    src_code, unit, factor = rng.choice(NGO_ITEMS[item])
                    std_qty = area["population"] * impact * rng.uniform(0.002, 0.02)
                    qty = max(1, round(std_qty / factor))
                    if defects.hit(rng, 0.01, "ngo", "unknown_item_code"):
                        src_code = src_code.lower() + "-x"
                    lines.append({"item_code": src_code, "unit": unit, "quantity": qty})
                ref = rng.choice([event["local_name"], event["international_name"],
                                  f"TY {event['local_name'].upper()}", event["event_code"]])
                location = {"province": area["province_name"], "municipality": area["name"]}
                if defects.hit(rng, 0.02, "ngo", "missing_location"):
                    del location["municipality"]
                elif defects.hit(rng, 0.05, "ngo", "location_name_variant"):
                    location["municipality"] = name_variant(rng, area["name"])
                record = {
                    "distribution_id": f"{org}-{day:%Y%m%d}-{next(seq):06d}",
                    "organization": rng.choice(NGO_ORG_NAMES[org]),
                    "event_ref": ref,
                    "distributed_on": day.isoformat(),
                    "location": location,
                    "beneficiaries": {"families": round(area["population"] * impact * rng.uniform(0.002, 0.03))},
                    "items": lines,
                }
                ngo_by_year[day.year].append(record)
                totals["distribution_line_rows"] += len(lines)

        # ---- LGU response logs: request -> dispatch -> arrival -> completion
        for area, impact in areas:
            for _ in range(round(impact * rng.uniform(3, 15) * math.log10(area["population"]))):
                rtype = rng.choices(list(REQUEST_TYPES), weights=[30, 15, 25, 15, 15])[0]
                units, base_dispatch, on_site = REQUEST_TYPES[rtype]
                priority = rng.choices(["P1", "P2", "P3"], weights=[25, 45, 30])[0]
                urgency = {"P1": 0.5, "P2": 1.0, "P3": 1.8}[priority]
                requested = datetime.combine(start, datetime.min.time()) + timedelta(
                    hours=rng.uniform(-12, 24 * ((end - start).days + 2)))
                dispatched = requested + timedelta(hours=rng.expovariate(1 / (base_dispatch * urgency)) + 0.1)
                arrived = dispatched + timedelta(hours=rng.uniform(0.3, 2) * (1 + 3 * impact))
                completed = arrived + timedelta(hours=rng.expovariate(1 / on_site) + 0.25)
                ts = lambda t: t.strftime("%Y-%m-%d %H:%M")  # noqa: E731
                r = {
                    "request_id": f"{area['psgc_code'][:7]}-{event['local_name'][:4].upper()}{start:%y}-{next(seq):06d}",
                    "incident": event["local_name"], "province": area["province_name"],
                    "lgu_name": area["name"], "request_type": rtype, "priority": priority,
                    "requested_at": ts(requested), "dispatched_at": ts(dispatched),
                    "arrived_at": ts(arrived), "completed_at": ts(completed),
                    "responding_unit": rng.choice(units),
                    "personnel_count": str(rng.randint(2, 12) + (6 if rtype == "RESCUE" else 0)),
                }
                if defects.hit(rng, 0.03, "lgu", "not_completed"):
                    r["completed_at"] = ""
                if defects.hit(rng, 0.01, "lgu", "arrival_before_dispatch"):
                    r["arrived_at"] = ts(dispatched - timedelta(minutes=rng.randint(5, 90)))
                if defects.hit(rng, 0.01, "lgu", "unknown_request_type"):
                    r["request_type"] = rng.choice(["RESQ", "Medical", "OTHERS"])
                if defects.hit(rng, 0.04, "lgu", "location_name_variant"):
                    r["lgu_name"] = name_variant(rng, r["lgu_name"])
                lgu_rows.append(r)
                totals["response_action_rows"] += 1

    write_csv(SOURCES_DIR / "pagasa" / "tc_bulletins.csv", pagasa_rows)
    for year, records in sorted(ngo_by_year.items()):
        with open(SOURCES_DIR / "ngo" / f"distributions_{year}.json", "w", encoding="utf-8") as f:
            json.dump(records, f, indent=1, ensure_ascii=False)
    write_csv(SOURCES_DIR / "lgu" / "response_logs.csv", lgu_rows)

    manifest = {"seed": seed, "events": len(events), "expected_rows": dict(totals),
                "planted_defects": dict(sorted(defects.counts.items()))}
    (SOURCES_DIR / "_defect_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def write_csv(path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=271)
    generate(parser.parse_args().seed)
