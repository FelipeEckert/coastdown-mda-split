# Split PDF report implementation plan

## Scope and phases

1. **Scaffold (completed):** canonical export contract, reusable ReportLab print
   styles, `reportlab>=5.0.1`, focused tests and project tracking.
2. **Rendering (Pages 1-3 implemented):** an A4 landscape summary followed by
   measured High/Low runs, with structural checks, canonical values, PT/EN labels
   and visual verification. Page 2 now includes compact tables and run curves.
   Page 3 presents pair composition and stored corrected coefficients. Page 4
   remains deferred; no existing export changes.
3. **Results integration (implemented):** explicit PDF metadata dialog and
   generation/download alongside Excel, with PT/EN labels and per-test metadata.
   PDF bytes are generated only on the final action and are not cached across edits.

## Data contract and ownership

`reports.split_pdf_report.export_split_final_results_to_pdf` implements this API:

```python
def export_split_final_results_to_pdf(
    *, final_results: dict, vehicle_data: dict, deviation_analysis: dict,
    graph_series: list[dict], test_name: str, generated_at: datetime,
    test_metadata: dict | None = None, language: str = "pt",
) -> bytes:
    ...  # Returns summary + measured-run PDF bytes from BytesIO.
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
Results stores report edits in `tests[active_test_id]["test_metadata"]` and
prefills from saved edits, test fields and current vehicle/test-date fields.
Equipment uses logger/vbox/weather_station keys; the existing meteo alias is
accepted. Current Split configuration is projected at export time and not
duplicated into saved report metadata. Comments are optional and, when supplied,
appear beside the test name in the existing Page 1 subtitle.

Blank optional report metadata now prints `Não informado` / `Not provided`;
literal `N/A` is reserved for metadata explicitly marked not applicable. This
supersedes earlier metadata N/A defaults below, while numerical missing-data
behavior remains unchanged. Raw blanks are saved without localized placeholders.
The dialog shows a subtle missing-metadata notice and never requires optional
fields. Existing page geometry and calculation ownership remain unchanged.

The Results handoff uses its existing summary, normalized vehicle snapshot and
deviation analysis. It consumes saved per-test `graph_series` when present;
otherwise chart panels remain unavailable. It does not reconstruct cumulative
times, prepare graph series or calculate missing directional energy. Dialog
state is dismissed/reset on test switches; PDF generation uses a fresh captured
snapshot and no download remains after a metadata edit without regeneration.
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

Sections 1-3 are rendered. Section 4 describes future work.
Page 1 contains final metrics, test/vehicle tables, masses, method/configuration,
equipment, the supplied time status and six supplied time checks, then a distinct
coefficient-CV diagnostic section. The footer shows page number, explicit
generation timestamp (including offset if supplied), and software identity.
It uses `num_pairs` directly; it does not recount or select pairs.

The approved visual guide is `docs/report-reference/split_report_layout.png`.
Page 1 follows its four rounded KPI cards, two side-by-side framed information
panels, three equal-height Method/Configuration/Equipment cards, and separate
boxed normative and diagnostic sections. Light blue title bands, navy hierarchy
and text-bearing status badges separate the sections without relying on color.
Badge colors follow the supplied pass flags only. Method-card semicolon-separated
metadata wraps onto separate lines without changing its values.

The header uses the existing `assets/hyundai_logo.png` unchanged, on a small navy
backing for its white artwork, with the original aspect ratio preserved. If the
file is absent the header is text-only. No new or recreated logo is required.
The footer additionally repeats the supplied service/report identifiers.

Required structures are dictionaries for final results, vehicle data and
deviation analysis, a `selected_pairs` list and a `time_summary` dictionary.
Empty supplied structures are allowed and display N/A; no scientific validity
checks are run. `generated_at` must be a datetime and language must be pt/en.
The renderer preserves signs and units, rounding only for presentation: F0 and
energy to 4 decimals, F2 to 6, masses/CVs/time percentages/limits to 2.
Optional method/configuration/equipment values come only from test metadata;
missing configuration is not inferred from a selected pair or normative defaults.

Page 1 fails with a readable ValueError when its summary content exceeds the
page. Page 2 begins with an explicit page break and stays on one landscape page.
No rows or curves are silently clipped, omitted or shrunk. Excessive table width,
row height or legend content raises a readable layout error. Footers use the actual current page number,
without an inaccurate fixed total or a second rendering pass.

### Measured-run contract (section 2)

- Read only `final_results.selected_pairs` and its four canonical `high_plus`,
  `high_minus`, `low_plus`, `low_minus` records; direction comes from that saved
  component identity. Do not reselect pairs or reparse the source files.
- One run snapshot per row, ordered by first occurrence within High or Low.
  Identified records repeated with identical full record/weather snapshots are
  collapsed. Different files, times or weather snapshots remain separate rows;
  unidentifiable records are not deduplicated. No conflicting values are averaged.
- Subinterval columns are the stable union of supplied `subintervals` labels
  and stored time-mapping keys. Read `subinterval_times_s` as an aligned list or
  label-keyed dictionary and read total `delta_t_s` directly. Missing values are
  N/A, never a recomputed sum or a graph-derived time. Reject duplicate labels,
  unlabeled extra times and malformed shapes rather than silently losing data.
- Weather comes from that component's `ambient_by_component`, then
  `weather_components`, then the record's `weather_sync` when the earlier
  snapshot is absent/empty. Read saved temperature, pressure, wind and their
  established aliases only. Never substitute pair averages, fixed correction
  inputs, another run's weather or a new synchronization calculation.
- Source/synchronization/warning details remain in the supplied snapshot but are
  omitted from Page 2, as requested in the approved visual refinement. Page 1
  normative/diagnostic warnings are unchanged.
- Follow `docs/report-reference/split_report_layout_page2.png`: four equal-width
  tables in one row (High times, High climate, Low times, Low climate), then a
  pale heading band and two full-width charts stacked High above Low. Run labels
  include the saved +/- direction. White background, light borders, 8 pt cells;
  times show 3 decimals, temperature 1, pressure/wind 2.
- Column labels remain dynamic. A minimum 30 pt column width accommodates four
  subinterval columns; wider sets raise a layout error. Charts share the remaining
  height with a 130 pt minimum each. Excessive rows or legends also raise errors;
  this fixed-page layout supersedes the earlier continuation/column-band design.
- Empty tables show N/A. Legacy aggregate records keep their stored total;
  missing subinterval values stay N/A without reconstructing them from curves.

### Supplied graph contract (Page 2)

- The caller supplies consistent, selected-run `graph_series` snapshots with
  public run IDs and +/- direction, partitioned by `interval_name` high/low.
  Each entry requires a record dictionary and aligned finite numeric `times_s`
  and `speeds_kmh` lists/tuples containing at least two points. Invalid structures
  raise ValueError; an empty series list displays unavailable chart panels.
- ReportLab LinePlot renders vector polylines through the exact supplied points.
  Do not call graph preparation helpers, sum subintervals, fit/smooth curves,
  resample, convert units or reconstruct endpoints. Axis tick/range selection is
  presentation only. The caller remains responsible for snapshot consistency.
- Legends use the supplied run ID and direction, with dashed lines for minus
  runs. `data_mode=aggregate` gets an explicit endpoints label (PT/EN). Missing
  curves are never fabricated from the run tables. No plotting dependency added.

1. **Test, vehicle and final summary:** available test metadata, vehicle and mass
   chain, configured intervals, selected-pair count, final F0/F2 and energy,
   canonical normative time status and warnings.
2. **Run times and environment:** High/Low +/- runs, dynamic subinterval columns,
   total times, conditions associated with each run and supplied deceleration
   curves. Never assume separate input files; verbose trace details are omitted.
3. **Selected pairs and corrected coefficients:** two-column pair blocks with
   High+, Low+, High-, Low- run IDs, vertically merged corrected directional
   values and a highlighted stored pair mean. No uncorrected coefficients.
4. **Coefficients and normative results:** uncorrected and corrected directional
   and pair coefficients, stored energy, final values, diagnostic coefficient CVs,
   normative time metrics with supplied limits/statuses, and warnings.

## Rendering architecture and print defaults

### Page 3 corrected-pair contract

Read `final_results.selected_pairs` in supplied order without reselecting or
deduplicating pairs. Each block uses the stored `id` and four canonical run
records. Plus/minus corrected coefficients come only from `F0_plus`, `F2_plus`,
`F0_minus`, `F2_minus`. The mean row reads `F0_mean`, `F2_mean`, and `energy`.
Optional stored `energy_plus` / `energy_minus` supply directional energy; absent
values are N/A. The existing Results UI computes directional energy on demand,
so those values are not guaranteed to be present in canonical pair snapshots.
Do not call that helper, calculate energy, average directions, or fall back to
uncorrected coefficients. These optional fields stay within the existing dict
contract; no new top-level input or upstream behavior is introduced.

The page title is `Pares e coeficientes | Split` (PT) / `Pairs and coefficients |
Split` (EN). Native Table spans merge columns F0/F2/Energy separately across
High+/Low+ and High-/Low-. Preserve units N, N/(km/h)², MJ/km and existing display
precision (4/6/4 decimals). Empty selection gets an unavailable note. Blocks
flow left-to-right in two columns, with an empty right cell for an odd count.
A dedicated PageTemplate starts on page 3; oversized content raises a readable
error instead of clipping pairs or adding Page 4. Pages 1-2 retain their layout.

At the bottom of Page 3, `Resultados finais` / `Final results` lists each
selected pair's stored `F0_mean`, `F2_mean` and `energy`. A highlighted consolidated
row reads `final_results.mean_f0`, `mean_f2` and `mean_energy` directly, using
4/6/4 display decimals. Never average pair rows in reporting, even when supplied
consolidated values differ. Missing numerical values remain N/A. Compact pair
blocks leave space for the summary; all content must still fit Page 3.

- `reports/__init__.py`: package identity only, no eager application imports.
- `reports/split_pdf_report.py`: public entry point; Platypus story of paragraphs
  and tables in a BaseDocTemplate with a zero-padding Frame, written into
  `BytesIO` and returned as PDF bytes. A PageTemplate callback draws the header
  and footer. Separate summary/run PageTemplates enforce both page boundaries.
- `reports/report_styles.py`: landscape A4, 8 mm side margins matching the visual
  reference, white background,
  navy headings, dark text, restrained table shading; Helvetica/Helvetica-Bold,
  10 pt body and 9 pt tables. Fresh styles per report prevent shared mutation.
  The title is 24 pt, KPIs 22 pt, section headings 12 pt and footer text 7 pt.
- Charts use ReportLab vector drawings from supplied series; no Plotly
  image-export dependency. Wrap table text and escape external Paragraph markup;
  fail explicitly when the approved fixed-page layout cannot fit legibly.
- Status text and direction/line labels must work without color. PT accents,
  coefficient notation and unit glyphs require visual checks before rendering
  ships. No custom fonts or newly created report assets are required.

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
The updated three-page synthetic sample is `output/pdf/split_report_sample.pdf`,
generated from `tests.test_split_pdf_report.sample_run_inputs()` through the public
exporter. The earlier Page 1 sample remains a visual baseline. Run tests cover
stored totals differing from interval sums, run-specific weather, list/mapping
times, missing data, duplicates/distinct sources, shape errors, wide custom
intervals, PT/EN, graph shape errors, exact point preservation, endpoint labels,
unavailable curves, layout overflow and unchanged Page 1 content. Inspect both
sample pages plus EN and missing-data variants before delivery. Compare Pages 1-2
pixels to the previous sample. Pair checks cover exact corrected values, supplied
means differing from directional averages, unavailable directional energy, merged
cells, odd block counts, empty selection and overflow. Page 4 remains deferred.
