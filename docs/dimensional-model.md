# DRIW Dimensional Model

Star schema in the `dw` schema. All facts share conformed dimensions, so damage,
evacuation, relief and response can be analysed side by side for the same event and place.

## Fact tables

| Fact | Type | Grain (one row per…) | Measures |
|---|---|---|---|
| `fact_damage_assessment` | Transaction | event × city/municipality × damage category (latest sitrep) | dead, injured, missing, affected families, affected persons, houses partially / totally damaged, cost (PHP) |
| `fact_evacuation_snapshot` | Periodic snapshot | evacuation center × day | families inside, persons inside, capacity (families). **Semi-additive**: sum across centers, never across days (use average or end-of-period) |
| `fact_resource_distribution` | Transaction | distribution line item (event, date, city/municipality, organization, item) | quantity in standard unit, value (PHP), beneficiary families |
| `fact_response_action` | Accumulating snapshot | response request | hours to dispatch, hours to arrive, hours to complete, personnel deployed; four role-playing dates (requested, dispatched, arrived, completed) |

## Dimensions

| Dimension | Key source | Notes |
|---|---|---|
| `dim_date` | generated | Day, month, quarter, year, PH typhoon season flag. Role-playing in `fact_response_action`. |
| `dim_location` | PSGC 10-digit code | Region → Province → City/Municipality hierarchy, population. **SCD Type 2**: boundary and name changes (e.g. Maguindanao split, 2022) keep history. |
| `dim_event` | PAGASA | Local + international name, hazard type, category, max signal, start/end dates. |
| `dim_organization` | `ref.organization` | Agency, NGO, LGU, international; source name variants resolved via aliases. |
| `dim_resource` | `ref.resource_item` | Item, category (Food, Water, Non-Food, Medical, Shelter), standard unit, unit cost. |
| `dim_evacuation_center` | DROMIC EC code | Type (school, covered court, gym…), barangay, capacity. |
| `dim_damage_category` | fixed list | Population, Housing, Infrastructure, Agriculture. |
| `dim_response_type` | LGU logs | Rescue, medical evacuation, evacuation assistance, road clearing, relief delivery; priority. |
| `dim_source_system` | `meta.load_batch` | Lineage: which source and batch each fact row came from. |

## Bus matrix

| Fact \ Dimension | Date | Location | Event | Organization | Resource | Evac Center | Damage Cat | Response Type | Source |
|---|---|---|---|---|---|---|---|---|---|
| Damage Assessment | ✓ | ✓ | ✓ | | | | ✓ | | ✓ |
| Evacuation Snapshot | ✓ | ✓ | ✓ | ✓ | | ✓ | | | ✓ |
| Resource Distribution | ✓ | ✓ | ✓ | ✓ | ✓ | | | | ✓ |
| Response Action | ✓ ×4 | ✓ | ✓ | ✓ | | | | ✓ | ✓ |
