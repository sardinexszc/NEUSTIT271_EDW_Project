# Enterprise Positioning and Data Exchange

## 1. Why an enterprise data warehouse has no content management system

A content management system (CMS) is for creating and editing content: web pages, documents,
records typed in by users. An enterprise data warehouse (EDW) has a different job. It **receives**
data from the systems where data is entered, **integrates** it, **keeps its history**, and serves it
for analysis. The three kinds of system sit in a chain:

| Stage | Purpose | In disaster response |
|---|---|---|
| Source (operational) systems | Where data is entered and edited day to day | DROMIC workbooks, NDRRMC situation reports, LGU response logs, NGO distribution records, PAGASA bulletins |
| Enterprise data warehouse | Integrate, clean, historize and govern; read-only for its users | **DRIW** |
| Business intelligence | Present and explore | The DRIW dashboards, CSV and API exports |

DRIW deliberately has no data-entry screens. Data can enter only through the controlled ETL
pipeline, so every value is validated by the 36 data-quality rules, traceable to the file and row it
came from, and reproducible by re-running the pipeline. A screen that let users edit warehouse
figures would break all three guarantees. Where a CMS or portal belongs is upstream, as a way for an
LGU to *submit* a file (see §3), or downstream, to publish reports. It is never the warehouse itself.

### What makes DRIW an enterprise data warehouse

Inmon's classic definition calls a data warehouse subject-oriented, integrated, time-variant and
non-volatile. DRIW meets each one:

| Characteristic | Evidence in DRIW |
|---|---|
| Subject-oriented | Organized around four subjects of disaster response (damage, evacuation, relief, response), not around any one agency's forms. |
| Integrated | Five sources in three formats conformed to one geography (PSGC codes), one event list (PAGASA names and aliases), one set of organizations and one set of relief units. |
| Time-variant | Six years of events (2020–2025); every fact is dated; locations keep their history (SCD Type 2, e.g. the 2022 Maguindanao split). |
| Non-volatile | Users can only read; loads happen through the pipeline; a full rebuild reproduces the same warehouse (a test enforces this). |

"Enterprise" means the warehouse serves the whole organization, across agencies, from one governed
model. DRIW has the capabilities that implies:

| Enterprise capability | Where it is in DRIW |
|---|---|
| Integration of many source systems | Five simulated agency systems (Chapter 4) |
| Conformed dimensions across subjects | Bus matrix: date, location and event shared by all four facts (Chapter 2) |
| Metadata and lineage | Data dictionary generated from the catalog; every row traces to its source batch (Chapter 3) |
| Data-quality management | Rule catalog, quarantine, reconciliation 19/19 (Chapter 5) |
| Security and governance | Four roles, row-level security by region, read-only web role (Chapter 6) |
| Serving many audiences | Executive, Operations and Logistics dashboards; CSV and API exports (Chapter 7) |
| Reliability | 148 automated checks, run on every change (Chapter 8) |
| Room to grow | Standard PostgreSQL; the same migrations run on a cloud database such as Supabase |

## 2. Data exchange with LGUs and national agencies today

### Importing

DRIW imports files in the standard layout of each report type. A file from any LGU or national
agency is accepted if it follows that layout.

| Report type | File format | Folder | Layout |
|---|---|---|---|
| DSWD DROMIC evacuation report | **Excel (.xlsx)** | `data/sources/dromic/` | First sheet; one header row, then 12 columns: report date, disaster, region, province, city/municipality, barangay, evacuation-center code, center name, center type, capacity (families), families inside, persons inside |
| NDRRMC situation report | CSV | `data/sources/ndrrmc/` | Header names as in `raw.ndrrmc_damage_report` |
| LGU / MDRRMO response log | CSV | `data/sources/lgu/` | Header names as in `raw.lgu_response_log` |
| PAGASA bulletin | CSV | `data/sources/pagasa/` | Header names as in `raw.pagasa_event` |
| NGO relief distribution | JSON | `data/sources/ngo/` | One record per distribution, with its item lines |

Any spreadsheet program can produce the CSV formats (Excel: *Save As › CSV UTF-8*). To load new
files, copy them into the folder and run:

```bash
.venv/Scripts/python ingestion/pipeline.py raw dbt export
```

Each file becomes one load batch. The data-quality layer then does what an analyst would otherwise
do by hand: it matches misspelled place names to the official PSGC (for example "NAGA CITY" to
*City of Naga*), resolves event names written in local, international or "TY" form, converts units,
and standardizes dates. Rows it cannot fix are held in quarantine with the reason, so the
submitting office can correct and resend them.

### Exporting

| Export | Format | Who uses it |
|---|---|---|
| Download CSV on every dashboard table | CSV with raw values, opens directly in **Excel** | Analysts, LGU and agency staff |
| All-events table | CSV, 24 measures per event | Reporting, further analysis |
| PHP API (`/driw/api/marts.php`) | JSON | Other information systems; Excel or Power BI through a web query |
| Direct SQL by role | PostgreSQL (ODBC/JDBC from Excel, Power BI, Tableau) | Analysts (`driw_analyst`), regional officers (own region only) |

### What it does not do yet

Files must follow the standard layouts above; a workbook with different columns needs to be
rearranged first. Files are loaded by an operator, not uploaded by the LGU, and exports are CSV and
JSON rather than formatted Excel workbooks. §3 proposes how to close these gaps.

## 3. Recommended extensions

These are not implemented; they are the next steps toward a production service for LGUs and
national agencies.

| # | Extension | What it adds |
|---|---|---|
| 1 | **Standard Excel templates** per report type | Downloadable .xlsx files with drop-down lists (province, city/municipality and event taken from the warehouse), so submissions arrive clean |
| 2 | **Upload page with an instant validation report** | An LGU uploads its workbook; DRIW runs the quality rules and returns, row by row, what was accepted, corrected or rejected and why |
| 3 | **Column-mapping profiles** | Each LGU's own column headings mapped once to the standard layout, so existing forms can be used unchanged |
| 4 | **Excel workbook export** | Formatted .xlsx downloads with one sheet per table and a data-dictionary sheet |
| 5 | **Submission tracking** | A dashboard of which LGUs have reported for each event, and which are late or missing |
| 6 | **Sign-in mapped to roles** | LGU officers log in and see only their region, using the row-level security already in the database |
| 7 | **Scheduled, incremental loads** | Automatic nightly or hourly loads that add only new files, instead of a manual full reload |
| 8 | **Open-data publication** | Aggregated, anonymized figures in the shape of UNDRR / Sendai Framework indicators |

Extensions 1–4 together would let DRIW honestly be described as accepting Excel data from any LGU
or national DRRM office, in any layout, and returning it as Excel.
