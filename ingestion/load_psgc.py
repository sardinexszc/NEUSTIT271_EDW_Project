"""Load the official PSA PSGC publication (Excel) into ref.psgc.

Also writes two derived, committed CSVs used by the synthetic generator:
  data/reference/psgc_citymun.csv   cities/municipalities with province + region names
  data/reference/psgc_barangay.csv  barangays with their parent city/municipality

Usage: python ingestion/load_psgc.py [path/to/PSGC-...-Publication-Datafile.xlsx]
       (defaults to the newest PSGC*.xlsx in data/reference/)
"""

import csv
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

from common import REFERENCE_DIR, connect

# Highly urbanized / independent component cities carry their own province segment in the
# 10-digit code, so they have no "Prov" parent. Map them to their geographic province.
INDEPENDENT_CITY_PROVINCE = {
    "baguio": "Benguet", "angeles": "Pampanga", "olongapo": "Zambales", "lucena": "Quezon",
    "puerto princesa": "Palawan", "iloilo": "Iloilo", "bacolod": "Negros Occidental",
    "cebu": "Cebu", "lapu-lapu": "Cebu", "mandaue": "Cebu", "tacloban": "Leyte", "ormoc": "Leyte",
    "zamboanga": "Zamboanga del Sur", "isabela": "Basilan", "cagayan de oro": "Misamis Oriental",
    "iligan": "Lanao del Norte", "davao": "Davao del Sur", "general santos": "South Cotabato",
    "butuan": "Agusan del Norte", "santiago": "Isabela", "naga": "Camarines Sur",
    "dagupan": "Pangasinan", "cotabato": "Maguindanao del Norte",
}
NCR_REGION_PREFIX = "13"
CITYMUN_LEVELS = {"City", "Mun"}


def find_header(ws):
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=True), start=1):
        cells = [str(c or "").strip().lower() for c in row]
        if any("geographic level" in c for c in cells):
            return i, cells
    raise SystemExit(f"sheet '{ws.title}' has no 'Geographic Level' header")


def col(cells, *needles):
    for i, c in enumerate(cells):
        if all(n in c for n in needles):
            return i
    return None


def bare_city_name(name: str) -> str:
    n = name.lower().replace("city of ", "").replace(" city", "")
    return re.sub(r"\s*\(.*\)", "", n).strip()


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else max(REFERENCE_DIR.glob("PSGC*.xlsx"), default=None)
    if not path or not path.exists():
        raise SystemExit("PSGC workbook not found; see data/reference/README.md")
    publication = re.sub(r"[-_]", " ", path.stem).replace("Publication Datafile", "").strip()

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = next((s for s in wb.worksheets if s.title.strip().upper() == "PSGC"), wb.worksheets[0])
    header_row, cells = find_header(ws)
    c_code, c_name = col(cells, "psgc") or 0, col(cells, "name")
    c_level, c_class = col(cells, "geographic level"), col(cells, "city class")
    c_income, c_urban = col(cells, "income"), col(cells, "urban")
    c_pop = col(cells, "population")
    census = cells[c_pop].replace("population", "").strip().upper() if c_pop is not None else None

    units = {}
    for r in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if not r[c_code] or not r[c_level]:
            continue
        code = str(r[c_code]).split(".")[0].strip().zfill(10)
        pop = r[c_pop] if c_pop is not None else None
        units[code] = {
            "code": code,
            "name": re.sub(r"\s*\(Capital\)", "", str(r[c_name]).strip()),
            "level": str(r[c_level]).strip(),
            "city_class": (r[c_class] or None) if c_class is not None else None,
            "income": (str(r[c_income]).strip() or None) if c_income is not None and r[c_income] else None,
            "urban": (r[c_urban] or None) if c_urban is not None else None,
            "population": int(pop) if isinstance(pop, (int, float)) else None,
        }

    def parent(code: str, length: int, levels: set[str]) -> str | None:
        p = code[:length].ljust(10, "0")
        return p if p != code and p in units and units[p]["level"] in levels else None

    for u in units.values():
        code = u["code"]
        u["region_code"] = code[:2] + "0" * 8
        u["province_code"] = parent(code, 5, {"Prov"})
        u["city_muni_code"] = None
        if u["level"] == "Bgy":
            # nearest City/Mun ancestor (skips sub-municipalities such as Manila's districts)
            candidates = (code[:7] + "000", code[:6] + "0000", code[:5] + "00000")
            u["city_muni_code"] = next(
                (c for c in candidates if units.get(c, {}).get("level") in CITYMUN_LEVELS), None)

        # human-readable province for cities/municipalities
        if u["level"] in CITYMUN_LEVELS:
            if u["province_code"]:
                u["province_name"] = units[u["province_code"]]["name"]
            elif code.startswith(NCR_REGION_PREFIX):
                u["province_name"] = "Metro Manila"
            else:
                u["province_name"] = INDEPENDENT_CITY_PROVINCE.get(bare_city_name(u["name"]), u["name"])
            u["region_name"] = units.get(u["region_code"], {}).get("name", "")

    save_units(units, publication, census)


def save_units(units: dict, publication: str, census: str | None) -> None:
    """Write units to ref.psgc and the derived CSVs, then check events.csv provinces resolve.

    Each unit needs: code, name, level, region_code, province_code, city_muni_code, city_class,
    income, urban, population; cities/municipalities also province_name and region_name.
    A unit may carry population_estimate, used by the generator when no census figure exists.
    """
    with connect() as conn:
        conn.execute("truncate ref.psgc cascade")
        with conn.cursor().copy(
            "copy ref.psgc (psgc_code, name, geographic_level, region_code, province_code, city_muni_code, "
            "city_class, income_class, urban_rural, population, population_census, publication, province_name) "
            "from stdin"
        ) as copy:
            for u in units.values():
                copy.write_row([u["code"], u["name"], u["level"], u["region_code"], u["province_code"],
                                u["city_muni_code"], u["city_class"], u["income"], u["urban"],
                                u["population"], census, publication, u.get("province_name")])
        conn.commit()

    citymun = [u for u in units.values() if u["level"] in CITYMUN_LEVELS]
    with open(REFERENCE_DIR / "psgc_citymun.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["psgc_code", "name", "geographic_level", "province_name", "region_name", "population"])
        for u in sorted(citymun, key=lambda u: u["code"]):
            w.writerow([u["code"], u["name"], u["level"], u["province_name"], u["region_name"],
                        u["population"] or u.get("population_estimate") or ""])
    brgys = [u for u in units.values() if u["level"] == "Bgy"]
    with open(REFERENCE_DIR / "psgc_barangay.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["psgc_code", "name", "city_muni_code", "population"])
        for u in sorted(brgys, key=lambda u: u["code"]):
            w.writerow([u["code"], u["name"], u["city_muni_code"], u["population"] or ""])

    levels = {}
    for u in units.values():
        levels[u["level"]] = levels.get(u["level"], 0) + 1
    print(f"{publication}: {len(units):,} units {levels}; population column: {census}")

    # every province named in events.csv must resolve
    with open(REFERENCE_DIR / "events.csv", newline="", encoding="utf-8") as f:
        wanted = {p for e in csv.DictReader(f) for p in e["affected_provinces"].split(";")}
    known = {u["province_name"].lower() for u in citymun}
    missing = sorted(p for p in wanted if p.lower() not in known)
    print("all event provinces resolved" if not missing else f"UNRESOLVED event provinces: {missing}")


if __name__ == "__main__":
    main()
