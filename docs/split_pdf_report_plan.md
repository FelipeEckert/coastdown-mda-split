# Split PDF report implementation plan

## Scope and phases

1. **Scaffold (completed):** canonical export contract, reusable ReportLab print
   styles, `reportlab>=5.0.1`, focused tests and project tracking.
2. **Rendering (Page 1 implemented):** one A4 landscape summary page with
   structural checks, canonical values, PT/EN labels and visual verification.
   Sections/Pages 2-4 remain deferred; no assets or existing export changes.
3. **Results integration (later):** explicit PDF generation/download alongside
   Excel, PT/EN labels and cache invalidation from the complete report snapshot.

## Data contract and ownership

`reports.split_pdf_report.export_split_final_results_to_pdf` implements this API:

```python
def export_split_final_results_to_pdf(
    *, final_results: dict, vehicle_data: dict, deviation_analysis: dict,
    graph_series: list[dict], test_name: str, generated_at: datetime,
    test_metadata: dict | None = None, language: str = "pt",
) -> bytes:
    ...  # Returns a one-page PDF as bytes from BytesIO.
```

The caller supplies one consistent snapshot, prepared outside `reports`:

| Input | Canonical content/source |
| --- | --- |
| `final_results` | Already produced `core.split_results.consolidate_split_final_results` output: means, energy, CVs, counts, warnings and `selected_pairs`. This nested list is the sole pair source, preserving order. |
| Selected pairs | Canonical High/Low +/- records; configured speeds, total/subinterval times, filenames, run IDs, columns and source hashes when available; `f0_prime_*`, `f2_prime_*`, `F0_*`, `F2_*`, stored energy, directional conditions used and `ambient_by_component`. |
| `vehicle_data` | Vehicle identification and already normalized running-order, test, rotational-equivalent and effective masses prepared by the caller. No test-level metadata. |
| `deviation_analysis` | Already produced `core.split_deviation_analysis` output: `time_summary`, `coefficient_summary`, `weather_summary`, supplied limits, statuses and warnings. |
| `graph_series` | Prepared series following `utils.split_graphs.build_split_run_plot_series`: `times_s`, `speeds_kmh`, `record`, `interval_name`, `direction`, `interval_rows`, `data_mode`. Preparation stays outside the PDF layer. |
| `test_metadata` | Optional dictionary of available test identification/traceability fields; see below. |
| Other metadata | Active `test_name`, explicit report `generated_at`, and `language` (`pt` default or `en`). |

Optional `test_metadata` keys: `test_date`, `responsible_engineer`, `operator`,
`driver`, `location`, `service_identifier`, `report_identifier`, `start_time`,
`end_time`, `method`, `configuration`, and `equipment`. Configuration/equipment
may retain structured caller data. Omitted metadata is unavailable, never
inferred. Do not move these fields into `vehicle_data`; historical test dates
stored there must be projected by the future caller into `test_metadata`.
The report-generation timestamp is not a fallback test date.
Optional `software_name` and `software_version` override the neutral identity
from `version.py` in the footer and PDF creator metadata. Explicit missing
software values print as N/A. Vehicle `model` and optional `vin` are displayed
without copying test-level fields into the vehicle section.

The PDF layer only formats and renders. Never call calculation, consolidation,
selection, parser, mass normalization, weather correction or normative-validation
helpers. In particular, do not reuse Results directional-energy helpers or the
Excel exporter: those paths perform calculations. No F0/F2, energy, CV or weather
averages may be calculated inside reporting. Preserve canonical signs and units
without coefficient conversion; use public run/pair labels with source identity
retained for traceability. Missing optional values display as unavailable, never
zero; structural checks reject missing required sections with readable
errors, without evaluating scientific validity. Do not mutate inputs.

Normative conformity follows `deviation_analysis["time_summary"]["passed"]`
(true/false/unknown), matching Results. Coefficient CVs are diagnostic; neither
the consolidated coefficient status nor the combined analysis status substitutes
for normative time conformity. Display supplied limits and warnings, not new
hardcoded thresholds. Missing directional energy stays unavailable.

## Report sections

Only section 1 is currently rendered. Sections 2-4 describe future work.
Page 1 contains final metrics, test/vehicle tables, masses, method/configuration,
equipment, the supplied time status and six supplied time checks, then a distinct
coefficient-CV diagnostic section. The footer shows page number, explicit
generation timestamp (including offset if supplied), and software identity.
It uses `num_pairs` directly; it does not recount or select pairs.

Required structures are dictionaries for final results, vehicle data and
deviation analysis, a `selected_pairs` list and a `time_summary` dictionary.
Empty supplied structures are allowed and display N/A; no scientific validity
checks are run. `generated_at` must be a datetime and language must be pt/en.
The renderer preserves signs and units, rounding only for presentation: F0 and
energy to 4 decimals, F2 to 6, masses/CVs/time percentages/limits to 2.
Optional method/configuration/equipment values come only from test metadata;
missing configuration is not inferred from a selected pair or normative defaults.

Page 1 fails with a readable ValueError when content exceeds the page or reserved
footer area. It never silently truncates, shrinks text or emits a second page.
Future detailed sections may paginate independently once implemented.

1. **Test, vehicle and final summary:** available test metadata, vehicle and mass
   chain, configured intervals, selected-pair count, final F0/F2 and energy,
   canonical normative time status and warnings.
2. **Run times and environment:** High/Low +/- runs, dynamic subinterval columns,
   total times, conditions actually used, synchronization information and
   file/run/column/interval traceability. Never assume separate input files.
3. **Deceleration graphs and selected pairs:** speed (km/h) against elapsed time
   (s), High/Low sections, public run labels, directional distinction and selected
   pair composition. Plot supplied points only; explicitly label aggregate
   endpoints and do not imply a measured continuous curve. Missing series get
   an unavailable-data note. Paginate dense charts rather than crowding legends.
4. **Coefficients and normative results:** uncorrected and corrected directional
   and pair coefficients, stored energy, final values, diagnostic coefficient CVs,
   normative time metrics with supplied limits/statuses, and warnings.

## Rendering architecture and print defaults

- `reports/__init__.py`: package identity only, no eager application imports.
- `reports/split_pdf_report.py`: public entry point; Platypus story of paragraphs
  and tables in a BaseDocTemplate with a zero-padding Frame, written into
  `BytesIO` and returned as PDF bytes. A PageTemplate callback draws the header
  and footer and prevents additional pages.
- `reports/report_styles.py`: landscape A4, 15 mm margins, white background,
  navy headings, dark text, restrained table shading; Helvetica/Helvetica-Bold,
  10 pt body and 9 pt tables. Fresh styles per report prevent shared mutation.
- Future charts use ReportLab vector drawings from supplied series; no Plotly
  image-export dependency. Repeat table headers, wrap long text, escape external
  text before Paragraph markup, and paginate instead of shrinking unreadably.
- Status text and direction/line labels must work without color. PT accents,
  coefficient notation and unit glyphs require visual checks before rendering
  ships. No custom fonts or report assets are required for this scaffold.

## Validation

Use the existing `.venv` interpreter. PDF content tests require `pypdf`; visual
QA uses `pypdfium2` when Poppler is unavailable. Install these inspection-only
tools with `python -m pip install pypdf pypdfium2`; the renderer itself only
requires ReportLab. Check report imports and run `pip check`, PDF unittests and existing
results/Excel export/graphs/deviation-analysis/export-cache regressions. Compile
changed Python files with `python -m py_compile`, scoped Ruff and `git diff --check`.
Stage only the intended files individually; do not commit.

Page 1 checks read actual PDF bytes with pypdf: one landscape page, canonical
values/signs/count/limits/statuses even for inconsistent sentinel inputs, missing
data, PT/EN text, literal escaped metadata, software identity, unchanged inputs,
structural errors, overflow and imports without application calculation modules.
The explicitly synthetic sample is `output/pdf/split_page_1_sample.pdf`, generated
from `tests.test_split_pdf_report.sample_inputs()` by calling the public exporter.
Inspect a rasterized sample, plus EN and missing-data variants, before delivery.
Future checks remain for graphs, detailed coefficient/run tables and pagination.
