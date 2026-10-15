-- Master / reference data used to conform the sources.

-- Philippine Standard Geographic Code (PSA). One row per geographic unit, all levels.
-- Loaded from the official PSA publication by ingestion/load_psgc.py.
create table if not exists ref.psgc (
    psgc_code         char(10) primary key,
    name              text     not null,
    geographic_level  text     not null,   -- Reg | Prov | Dist | City | Mun | SubMun | SGU | Bgy
    region_code       char(10),
    province_code     char(10),            -- null for NCR / independent cities without a province
    city_muni_code    char(10),
    city_class        text,                -- HUC | ICC | CC (component city) | null
    income_class      text,
    urban_rural       text,
    population        integer,
    population_census text,                -- e.g. '2020 CPH' or '2024 POPCEN'
    publication       text     not null    -- e.g. 'PSGC 2Q 2025' (which release this row came from)
);
create index if not exists psgc_level_idx on ref.psgc (geographic_level);
create index if not exists psgc_parent_idx on ref.psgc (city_muni_code);

-- Spelling variants seen in sources, mapped to the official PSGC code.
-- Populated by the data-quality process; reviewed manually.
create table if not exists ref.location_alias (
    alias_name        text     not null,
    alias_scope       text     not null,   -- 'Prov' or 'CityMun'
    psgc_code         char(10) not null references ref.psgc (psgc_code),
    match_method      text     not null,   -- exact | normalized | manual
    primary key (alias_name, alias_scope)
);

-- Canonical organizations and the names each source uses for them.
create table if not exists ref.organization (
    org_code          text primary key,
    org_name          text not null,
    org_type          text not null,       -- National Government | LGU | NGO | International
    parent_agency     text
);
create table if not exists ref.organization_alias (
    alias_name        text primary key,
    org_code          text not null references ref.organization (org_code)
);

-- Canonical relief items with a standard unit, plus each NGO's own item codes/units.
create table if not exists ref.resource_item (
    item_code         text primary key,
    item_name         text not null,
    category          text not null,       -- Food | Water | Non-Food | Medical | Shelter
    standard_unit     text not null,
    unit_cost_php     numeric(12, 2) not null
);
create table if not exists ref.resource_item_alias (
    source_item_code  text primary key,
    item_code         text not null references ref.resource_item (item_code),
    source_unit       text not null,
    to_standard_factor numeric(12, 4) not null   -- multiply source qty by this to get standard units
);
