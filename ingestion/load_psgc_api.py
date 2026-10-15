"""Load PSGC geography from the community JSON API (https://psgc.gitlab.io/api/) into ref.psgc.

Fallback for when the official PSA workbook cannot be downloaded (see load_psgc.py).
The API mirrors PSA codes and names but has NO population figures, so the derived
psgc_citymun.csv carries a population *estimate* (barangay count x average barangay
population) for the synthetic generator; ref.psgc.population stays null.

Responses are cached in data/reference/psgc_api/ (git-ignored).
"""

import json
import random
import urllib.request

from common import REFERENCE_DIR
from load_psgc import bare_city_name, save_units

API = "https://psgc.gitlab.io/api"
CACHE = REFERENCE_DIR / "psgc_api"
ENDPOINTS = ["regions", "provinces", "districts", "cities-municipalities", "sub-municipalities", "barangays"]

AVG_BARANGAY_POPULATION = 2_600       # ~109M people / ~42k barangays (2020 CPH)
CITY_POPULATION_FACTOR = 1.6          # city barangays are denser than municipal ones
MAX_POPULATION_ESTIMATE = 1_000_000   # proxy breaks down for cities with many tiny barangays (Manila)
# Cities the API leaves without a province (independent component cities outside NCR).
CITY_PROVINCE = {"isabela": "Basilan", "cotabato": "Maguindanao"}


def fetch(endpoint: str) -> list[dict]:
    path = CACHE / f"{endpoint}.json"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"downloading {API}/{endpoint}.json")
        with urllib.request.urlopen(f"{API}/{endpoint}.json", timeout=120) as r:
            path.write_bytes(r.read())
    return json.loads(path.read_text(encoding="utf-8"))


def unit(rec: dict, level: str, **extra) -> dict:
    return {"code": rec["psgc10DigitCode"], "name": rec["name"], "level": level,
            "region_code": None, "province_code": None, "city_muni_code": None,
            "city_class": None, "income": None, "urban": None, "population": None, **extra}


def main() -> None:
    data = {e: fetch(e) for e in ENDPOINTS}
    code10 = {r["code"]: r["psgc10DigitCode"]
              for e in ENDPOINTS for r in data[e]}            # API 9-digit code -> 10-digit PSGC
    regions = {r["code"]: r["name"] for r in data["regions"]}
    provinces = {p["code"]: p["name"] for p in data["provinces"]}
    sub_parent = {s["code"]: s.get("cityCode") or s.get("municipalityCode") for s in data["sub-municipalities"]}

    def c10(code):
        return code10.get(code) if code else None

    units = {}
    for r in data["regions"]:
        u = unit(r, "Reg"); u["region_code"] = u["code"]; units[u["code"]] = u
    for p in data["provinces"]:
        u = unit(p, "Prov", region_code=c10(p["regionCode"])); units[u["code"]] = u
    for d in data["districts"]:
        u = unit(d, "Dist", region_code=c10(d["regionCode"])); units[u["code"]] = u

    brgy_count = {}
    for b in data["barangays"]:
        parent = b.get("cityCode") or b.get("municipalityCode") or sub_parent.get(b.get("subMunicipalityCode"))
        brgy_count[parent] = brgy_count.get(parent, 0) + 1
        u = unit(b, "Bgy", region_code=c10(b["regionCode"]), province_code=c10(b.get("provinceCode")),
                 city_muni_code=c10(parent))
        units[u["code"]] = u
    for s in data["sub-municipalities"]:
        u = unit(s, "SubMun", region_code=c10(s["regionCode"]), city_muni_code=c10(sub_parent[s["code"]]))
        units[u["code"]] = u

    for c in data["cities-municipalities"]:
        is_city = c["isCity"]
        if c["provinceCode"]:
            province_name = provinces[c["provinceCode"]]
        elif c["regionCode"].startswith("13"):
            province_name = "Metro Manila"
        else:
            province_name = CITY_PROVINCE.get(bare_city_name(c["name"]), c["name"])
        rng = random.Random(c["code"])
        estimate = min(MAX_POPULATION_ESTIMATE, round(brgy_count.get(c["code"], 10) * AVG_BARANGAY_POPULATION
                         * (CITY_POPULATION_FACTOR if is_city else 1.0) * rng.uniform(0.8, 1.2)))
        u = unit(c, "City" if is_city else "Mun", region_code=c10(c["regionCode"]),
                 province_code=c10(c["provinceCode"]), province_name=province_name,
                 region_name=regions[c["regionCode"]], population_estimate=estimate)
        units[u["code"]] = u

    save_units(units, publication="PSGC community API (psgc.gitlab.io)", census=None)


if __name__ == "__main__":
    main()
