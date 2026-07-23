# Ponytail Repository Audit - 2026-07-20

## Scope

This is a documentation-only audit of the Coastdown MDA Split repository. It
focuses on dead and duplicated code, inherited Standard-method paths, Streamlit
state and navigation, compatibility surfaces, maintainability, and test gaps.
No application code, tests, formulas, validation rules, or domain behavior were
changed as part of the audit.

Findings are ordered by risk within each section. Actionable findings 1-20 are
completed; confirmed indirect-usage findings 21-26 are closed with preservation
decisions.

## Summary

| # | Title | Severity | Confidence | Recommended phase | Current status |
|---:|---|---|---|---|---|
| 1 | Split final status still uses non-normative coefficient variation | High | High | 4 | Completed |
| 2 | Fixed-condition inputs are ignored for new tests | High | High | 3 | Completed |
| 3 | Declared Streamlit minimum is incompatible with active API use | High | High | 3 | Completed |
| 4 | Export cache signature omits workbook-visible traceability | Medium | High | 4 | Completed |
| 5 | Successful parsing always writes a shared debug file | Medium | High | 2 | Completed |
| 6 | Unreferenced local functions remain in active modules | Low | High | 1 | Completed |
| 7 | Unused imports, constants, and dependencies | Low | High | 1 | Completed |
| 8 | Orphan desktop-GUI configuration module | Low | High | 1 | Completed |
| 9 | Duplicate corrected-pair implementation | Low | High | 6 | Completed |
| 10 | Main and nested tabs compute hidden content eagerly | Medium | High | 3 | Completed |
| 11 | Redundant derived session state | Low | Medium-High | 5 | Completed |
| 12 | Eager package initializers couple Split imports to legacy modules | Medium | High | 6 | Completed |
| 13 | Loader has mixed Standard/Split responsibility and extreme complexity | Medium | High | 7 | Completed |
| 14 | Stale state keys obscure the canonical Split model | Low | Medium-High | 5 | Completed |
| 15 | Project documentation no longer matches ownership | Low | High | 1 | Completed |
| 16 | Critical Streamlit orchestration is untested | High | High | 3 | Completed |
| 17 | Several tests enforce source text rather than behavior | Low | High | 5 | Completed |
| 18 | Inherited Standard pages and dependency island removed | Medium | High | 8 | Completed |
| 19 | Split coefficient sign guidance aligned to canonical code | High | High | 8 | Completed |
| 20 | Orphan translations and stale compatibility text removed | Low | High | 8 | Completed |
| 21 | Automatic-selection page is indirectly rendered | Informational | High | Preserve | Completed — preserve |
| 22 | Package initializers execute through submodule imports | Informational | High | Phase 6 prerequisite | Completed — preserve |
| 23 | Session and widget keys have dynamic references | Informational | High | Preserve | Completed — preserve |
| 24 | Plotly is dynamically imported and required | Informational | High | Preserve | Completed — preserve |
| 25 | Sample datasets have test and validation roles | Informational | High | Preserve | Completed — preserve |
| 26 | Compatibility aliases may serve persisted or external consumers | Informational | Medium-High | Phase 8 prerequisite | Completed — preserve |

## Potential Bugs

### 1. Split final status still uses non-normative coefficient variation

- **Severity:** High
- **Confidence:** High
- **Locations:** `core/split_results.py:139-151`;
  `pages/page_split_results.py:349-362`;
  `data/split_exporters.py:274`;
  `tasks/lessons.md`, section "Resultados Split: conformidade vem de
  time_summary, nao de conformity_status".
- **Evidence:** `conformity_status` is based on the 10% F0/F2 coefficient of
  variation. The consolidated card was corrected to use
  `analysis["time_summary"]["passed"]`, but `_render_coefficients()` still
  displays an overall conforming/nonconforming banner from
  `summary["conformity_status"]`. The Excel summary writes "Status final" from
  the same non-normative field. Existing exporter tests also encode high F0/F2
  variation as a failed final status.
- **Why it is a problem:** The user can receive conflicting normative outcomes
  on the same Results page and in its exported workbook. Project memory
  explicitly records coefficient CV as diagnostic-only for Split.
- **Risk:** Low implementation risk if the compatibility field remains
  available; high domain impact if left unchanged.
- **Recommended action:** Keep `conformity_status` for compatibility, but make
  all user-facing and exported final status fields use the Split time
  validation result. Label coefficient CV as diagnostic.
- **Validation:** Add two regressions: time validation passes with F0/F2 CV above
  10%, and time validation fails with F0/F2 CV below 10%. Verify both the UI
  status and workbook status.
- **Resolution (2026-07-20):** Both Results-page conformity banners and the
  Excel "Status final" now map `analysis["time_summary"]["passed"]` to
  conforming, nonconforming, or inconclusive. F0/F2 CV values and pass/fail
  statuses remain visible with explicit diagnostic labels.
- **Status:** Completed

### 2. Fixed-condition inputs are ignored for new tests

- **Severity:** High
- **Confidence:** High
- **Locations:** `app.py:1573-1589`, `app.py:1662-1663`;
  `pages/page_split_coefficient_calculation.py:313-331`.
- **Evidence:** The new-test dialog collects fixed temperature and pressure and
  stores them as `fixed_temperature` and `fixed_pressure`. Split calculation
  reads `split_fixed_temperature` and `split_fixed_pressure`, so it falls back
  to `20.0` and `101.325` instead of the dialog defaults `25` and `101.3` or the
  values entered by the user.
- **Why it is a problem:** The UI accepts environmental values that are not used
  by the Split calculation workflow.
- **Risk:** Low code risk; potentially high result impact because ambient inputs
  influence corrected results.
- **Recommended action:** Store the entered values in the canonical
  `split_fixed_*` state keys during new-test creation. Retain old keys only if a
  persisted-state migration needs them.
- **Validation:** Create a test with clearly non-default fixed values, reopen it,
  and verify the ambient values used by the calculation page.
- **Resolution (2026-07-20):** New fixed-condition tests write both canonical
  `split_fixed_*` keys and legacy aliases. Loading migrates legacy-only values
  before defaults while preserving canonical-key precedence.
- **Validation result:** Focused creation, save/load, switching, legacy
  migration, and canonical-precedence regressions cover the active app path.
- **Status:** Completed

### 3. Declared Streamlit minimum is incompatible with active API use

- **Severity:** High
- **Confidence:** High
- **Locations:** `requirements.txt`; `app.py:1726`.
- **Evidence:** The application calls `st.tabs()` with `default`, `key`, and
  `on_change`. Dynamic tab state and callbacks were introduced in Streamlit
  1.55, while the project declares `streamlit>=1.31.0`. The audited environment
  uses Streamlit 1.57.0, so tests there do not expose the lower-bound failure.
- **Why it is a problem:** A valid installation under the declared dependency
  range can fail during application rendering.
- **Risk:** Very low; this aligns metadata with behavior already required by the
  code.
- **Recommended action:** Change the lower bound to `streamlit>=1.55.0`.
- **Validation:** Install dependencies into a clean environment and start the
  application using the minimum declared version.
- **Resolution (2026-07-20):** Raised the declared minimum to Streamlit 1.55.0
  and added structured dependency validation. The complete dependency set
  resolved with Streamlit 1.55.0, and both AppTest and headless startup passed.
- **Status:** Completed

### 4. Export cache signature omits workbook-visible traceability

- **Severity:** Medium
- **Confidence:** High
- **Locations:** `data/split_exporters.py:57-67`;
  `core/split_deviation_analysis.py:27-57`.
- **Evidence:** `build_split_export_signature()` includes the selected-pair
  signature, final results, vehicle data, and deviation analysis. The pair
  signature includes identifiers, results, times, aggregate environment, and
  warnings, but omits filenames, run labels, subintervals, selection origin,
  and detailed component weather/corrected fields written to the workbook.
- **Why it is a problem:** A traceability-only change can return a cached
  workbook containing stale source information even when visible pair
  identifiers and numeric results remain stable.
- **Risk:** Low if signature construction is changed without altering workbook
  calculation behavior.
- **Recommended action:** Hash the exact immutable data projection used to build
  the workbook, or the complete frozen selected-pair records.
- **Validation:** Mutate a filename, run label, and subinterval independently
  without changing coefficients; each mutation must produce a cache miss and an
  updated workbook.
- **Resolution (2026-07-20):** The export signature now freezes complete copies
  of explicitly selected pair records instead of reusing the narrower deviation
  analysis signature. This covers filenames, run labels, subintervals, selection
  origin, corrected values, weather details, and future selected-pair
  traceability while leaving unselected records outside the cache key.
- **Status:** Completed

### 5. Successful parsing always writes a shared debug file

- **Severity:** Medium
- **Confidence:** High
- **Locations:** `data/loaders.py:40`, `data/loaders.py:168-170`,
  `data/loaders.py:238-240`, `data/loaders.py:276-278`,
  `data/loaders.py:293-295`, `data/loaders.py:364-366`,
  `data/loaders.py:513-515`, `data/loaders.py:523-524`,
  `data/loaders.py:536-538`.
- **Evidence:** The loader accumulates `debug_output` and writes
  `debug_vbox_date.txt` from multiple branches and unconditionally in `finally`.
  The audit test run updated this ignored file despite all tests passing.
- **Why it is a problem:** A read-only deployment can turn a successful parse
  into an exception during `finally`; concurrent Streamlit sessions also write
  the same process working-directory file and can overwrite each other's data.
- **Risk:** Low because the file is not consumed by application code.
- **Recommended action:** Remove the writes. If diagnostic output is still
  needed, use opt-in logging that cannot change the parser result.
- **Validation:** Parse successfully from a read-only working directory and run
  two parses concurrently. Confirm no shared artifact is created.
- **Resolution (2026-07-20):** Removed the unconditional successful-path write
  while preserving existing error-path diagnostics and parser behavior. Focused
  tests cover absent/existing files, denied writes, concurrency, and outputs.
- **Status:** Completed

## High-Confidence Low-Risk Removals

### 6. Unreferenced local functions remain in active modules

- **Severity:** Low
- **Confidence:** High for private helpers; Medium-High for the public-looking
  helper.
- **Locations:** `core/split_time_validation.py:93-95` (`_mean`);
  `pages/page_split_coefficient_calculation.py:95-121` (`_input_summary`);
  `:438-444` (`_ambient_mode_label`); `:811-824`
  (`_pair_component_rows`); `:827-828` (`_pair_weather_rows`); `:859-882`
  (`_corrected_result_rows`); `:973-1082` (`_render_comparison_area`);
  `:1287-1292` (`_graph_interval_label`); `:1631-1685`
  (`_render_calculated_pair_graphs`);
  `pages/page_split_final_comparison.py:141-145`
  (`get_selected_split_comparison_pairs`).
- **Evidence:** Repository-wide searches found no direct calls, callbacks,
  string-based references, test references, exports, or function-passing uses
  for these definitions. Tracing the private helper roots exposed seven more
  helpers used only inside the same orphaned UI cluster.
- **Why it is a problem:** They expand the maintenance and review surface and
  obscure the live calculation-page workflow.
- **Risk:** Low for underscore-prefixed helpers. The non-private comparison
  helper could be imported by an external consumer not visible in the
  repository.
- **Recommended action:** Delete the private helpers in one patch. Handle the
  public-looking helper separately after checking external entry points.
- **Validation:** Run the full suite and manually render calculation, graphs,
  automatic selection, final comparison, and results.
- **Status:** Completed. Removed 16 private helpers and their five now-unused
  imports. Retained public-looking `get_selected_split_comparison_pairs` for
  compatibility.

### 7. Unused imports, constants, and dependencies

- **Severity:** Low
- **Confidence:** High
- **Locations:** `app.py` (`APP_RELEASE_DATE`);
  `core/split_auto_selection.py` (`evaluate_split_constraint_satisfaction`,
  `validate_split_candidate_set`); `data/weather_loader.py:46-47`
  (`CROSSWIND_ALIASES`, `HEADWIND_ALIASES`); `requirements.txt` (`scipy`,
  `matplotlib`).
- **Evidence:** Ruff reported the active imports as unused. Repository-wide
  searches found no references to the weather constants and no imports of
  SciPy or Matplotlib. Plotly is excluded from this finding because graph code
  imports it dynamically. Full-suite validation proved that the two validator
  imports in `core/split_auto_selection.py` are compatibility re-exports, so
  they were retained explicitly.
- **Why it is a problem:** Unused dependencies increase installation size and
  failure surface; unused names create false ownership signals.
- **Risk:** Low, subject to one clean-environment install to detect undeclared
  plugin-style usage.
- **Recommended action:** Remove each unused name and dependency independently.
- **Validation:** Run Ruff, install from `requirements.txt` in a clean
  environment, run the full suite, and start the app.
- **Status:** Completed. Removed the unused release-date import, weather
  constants, SciPy, and Matplotlib. Retained the validator compatibility
  exports.

### 8. Orphan desktop-GUI configuration module

- **Severity:** Low
- **Confidence:** High within this repository
- **Location:** `config.py`, especially the PyQt5 `QFont` import.
- **Evidence:** No repository module, test, configuration file, or entry point
  imports `config.py`. It depends on PyQt5, which is not declared, and provides
  desktop-GUI configuration unrelated to Streamlit.
- **Why it is a problem:** It is inherited infrastructure with no demonstrated
  Split runtime role and cannot be imported in a clean project environment.
- **Risk:** Low internally; an undocumented external script could still import
  it.
- **Recommended action:** Confirm deployment and operator scripts do not import
  it, then delete the module.
- **Validation:** Run application startup, package/import smoke checks, and the
  full suite after removal.
- **Status:** Completed. Deleted the orphan module after startup, dependency,
  compile, Ruff, and full-suite validation passed.

## Safe Simplifications

### 9. Duplicate corrected-pair implementation

- **Severity:** Low
- **Confidence:** High
- **Locations:** Both corrected-pair names were implemented in
  `core/calculations.py` and `core/corrections.py`; `core/__init__.py` exports
  the correction-module names, while inherited page callers import the
  calculation-module names.
- **Evidence:** Before consolidation, the same-name definitions had identical
  executable bodies in both modules. Characterization tests now preserve the
  distinct rich and raw-value contracts, every import path, missing-value
  behavior, exception types/messages, return schemas/types, and exact numeric
  results. The compatibility wrappers also preserve their historical runtime
  lookup of `core.calculations.calcular_energia` without affecting direct
  correction-module calls.
- **Why it is a problem:** Fixes can diverge between two nominally equivalent
  paths, and the names do not establish which implementation owns the behavior.
- **Risk:** Medium because the legacy path and possible external imports may
  depend on the current symbols.
- **Recommended action:** Completed initially by consolidating the duplicated
  implementation. Finding 18 Batch 3 later removed the compatibility API after
  its last Standard page caller and exclusive tests were retired.
- **Validation:** Five focused characterization tests, all existing correction
  and calculation tests, 370 full-suite tests, scoped Ruff, compile validation,
  and `git diff --check` passed.
- **Status:** Completed. The duplication was removed first; the resulting
  compatibility-only module was removed with the retired Standard workflow.

### 10. Main and nested tabs compute hidden content eagerly

- **Severity:** Medium
- **Confidence:** High
- **Locations:** `app.py`; `pages/page_split_coefficient_calculation.py`;
  `pages/page_split_workflow.py`.
- **Evidence:** All five top-level page renderers execute after `st.tabs()`
  creation on every rerun. The nested calculation, graph, and automatic
  selection renderers do the same. Streamlit computes every tab by default;
  dynamic tabs support lazy execution only when code is guarded by each tab's
  `.open` state.
- **Why it is a problem:** Hidden pages perform avoidable calculations and can
  mutate state, build exports, or render graphs on unrelated interactions.
- **Risk:** Medium because some current state initialization may accidentally
  depend on eager execution.
- **Recommended action:** First characterize hidden-tab state mutations, then
  guard renderers with `.open`. Add a key/callback to nested tabs if required by
  the installed Streamlit API.
- **Validation:** Instrument or mock renderer calls and verify only the selected
  tab executes while navigation and saved test state remain unchanged.
- **Status:** Completed. Main, pair-analysis, and parser-review tabs now use
  Streamlit's keyed active-tab state and execute only the open renderer. The
  legacy comparison-selection repair runs after selected pages that can mutate
  pairs and before Results consumes them, so Results no longer depends on hidden
  Final Comparison execution.

### 11. Redundant derived session state

- **Severity:** Low
- **Confidence:** Medium-High
- **Locations:** `pages/page_split_final_comparison.py:562`;
  `app.py:1486`; `pages/page_split_results.py:482-484`.
- **Evidence:** `split_final_results` is written by Final Comparison. The active
  Results page recalculates from `split_comparison_pairs`, while the sidebar
  only reads `split_final_results` to display a count.
- **Why it is a problem:** Two sources can disagree after edits, and more data
  must be synchronized and persisted than the active workflow needs.
- **Risk:** Medium because old saved tests may contain only the derived key or
  external code may read it.
- **Recommended action:** Derive the sidebar count from canonical comparison
  pairs. Retain a compatibility read or migration for older snapshots before
  removing the key.
- **Validation:** Load current and legacy saved-state shapes, edit selected
  pairs, and confirm sidebar and Results counts remain consistent.
- **Resolution (2026-07-22):** `split_comparison_pairs` is now the canonical
  source for current final-result availability and selected-pair counts. New
  states, selection changes, invalidation, and Final Comparison navigation no
  longer write redundant `split_final_results` snapshots. During the migration
  window, legacy summaries remain readable; complete legacy `selected_pairs`
  lists migrate only when their stable IDs are unique, every pair is explicitly
  selected and valid under the current corrected-pair contract, and all supplied
  counts agree. Aggregate-only summaries survive passive rendering and are
  reported explicitly without inventing missing pair data.
- **Validation result:** Focused migration, sidebar, Results, switching, and
  save/load tests cover canonical-only, both-key, complete legacy-only,
  aggregate-only, malformed, duplicate, inconsistent, and incomplete legacy
  states, including idempotence and ambient invalidation. The 397-test full
  suite, scoped Ruff, compile validation, Streamlit startup health check, and
  diff hygiene pass.
- **Status:** Completed

## Maintainability Improvements

### 12. Eager package initializers couple Split imports to legacy modules

- **Severity:** Medium
- **Confidence:** High
- **Locations:** `core/__init__.py:8-25`; `data/__init__.py:6-24`.
- **Evidence:** Importing a Split submodule first executes its package
  initializer. Those initializers eagerly import legacy calculations,
  corrections, and Standard exporter infrastructure, including optional-heavy
  dependencies.
- **Why it is a problem:** Split modules cannot be imported independently, and
  dead-looking Standard code remains transitively live solely through package
  re-exports.
- **Risk:** Medium because callers may rely on `from core import ...` or
  `from data import ...` aliases.
- **Recommended action:** Convert repository callers to direct submodule
  imports. Keep only proven compatibility re-exports, then reduce initializer
  contents.
- **Validation:** Import every Split submodule with legacy/optional dependencies
  unavailable, and search for external documented import examples before
  removing aliases.
- **Resolution (2026-07-22):** `core` and `data` now resolve their existing
  package-level functions and module attributes lazily through module-level
  `__getattr__`. The public `__all__` lists, object identity, import errors on
  actual access, discoverability, and ambiguous compatibility aliases are
  preserved; no export was removed. Repository production callers already use
  direct submodule imports, so no caller rewrite was needed.
- **Validation result:** Focused tests cover dependency-free representative
  Split imports, all supported `from core import ...` and `from data import ...`
  exports, stable eager-era identity across source-module monkeypatching, exact
  deferred dependency errors, and both package/submodule import orders. The
  121-test calculation, correction, loader, and exporter regression group, the
  376-test full suite, Ruff, compile checks, a Streamlit `AppTest` startup smoke
  test, and diff hygiene pass.
- **Status:** Completed

### 13. Loader has mixed Standard/Split responsibility and extreme complexity

- **Severity:** Medium
- **Confidence:** High
- **Location:** `data/loaders.py:23-539`,
  `carregar_dados_csv_robusto`.
- **Evidence:** The function mixes neutral file loading, date/time parsing,
  Standard/Split branching, fallbacks, diagnostics, and output adaptation.
  Ruff reports cyclomatic complexity 69, 84 branches, and 325 statements.
  `is_alta` is propagated through callers and tests but is not used inside the
  implementation; `using_split_method` controls the method branch.
- **Why it is a problem:** A change for one format can regress another method,
  and the current structure makes it difficult to prove Split behavior without
  revalidating every legacy branch.
- **Risk:** High for a broad rewrite because this is a format boundary with many
  real-world variants and compatibility paths.
- **Recommended action:** Do not rewrite it wholesale. First remove the debug
  side effect and add characterization coverage; then extract only neutral I/O
  and explicit Standard/Split adapters in small patches.
- **Validation:** Preserve the complete parser matrix: separate files, combined
  file, full coastdown, custom intervals, missing-interval warnings, direction,
  traceability, legacy layouts, and representative real VBOX samples.
- **First low-risk phase (2026-07-22):** Characterization now fixes the current
  Standard and Split outputs, comma-only data-table behavior, decimal point and
  quoted decimal comma conversion, UTF-8/ISO-8859-1 handling, header/date/time
  failures, empty/read failures, and `is_alta` equivalence. Raw UTF-8-tolerant
  line reading moved unchanged into the private `_read_text_lines` helper;
  date parsing, fixed header position, delimiter behavior, normalization,
  method branches, warnings, fallbacks, and exception translation did not move.
  `is_alta` remains in the public signature solely for compatibility.
- **Validation result:** The same 14 public characterization cases pass before
  and after extraction, two direct helper checks pass, the 82-test loader/parser
  matrix and 423-test full suite pass, and scoped Ruff, compile, representative
  Standard/Split sample imports, Streamlit startup, and diff hygiene pass.
- **Second neutral phase (2026-07-22):** Fixed row-15 header construction and
  the existing comma-only Pandas read configuration moved into the private
  `_read_coastdown_table` helper. All 11 Split coastdown fixtures now have
  explicit row/run expectations. The ISO-8859-1 meteo fixture remains owned by
  `data/weather_loader.py`; integration coverage fixes its 9,476-record count,
  normalized keys, timestamps, numeric values, raw ordering break, and duplicate
  timestamps without changing that loader.
- **Second-phase validation:** The same 29 characterization/integration tests
  pass before and after extraction. The 16 focused, 62 coastdown, 33 meteo, and
  13 sample-data tests pass, as do the 423-test full suite, scoped Ruff, compile,
  Streamlit startup, and diff checks.
- **Third neutral phase (2026-07-22):** The existing alias lookup and required
  normalized-column check moved unchanged into `_validate_coastdown_columns`
  after the Pandas read. Header normalization remains before Pandas. Coverage
  now fixes the two real Standard layouts plus BOM, whitespace, capitalization,
  duplicate, empty, unexpected, and missing-column behavior without accepting
  new names.
- **Third-phase validation:** The same 19 public characterizations pass before
  and after extraction, with one narrow helper check. The 5 focused, 20 loader,
  66 coastdown, and 13 sample-data tests pass, as do the 427-test full suite,
  scoped Ruff, compile, Streamlit startup, and diff checks.
- **Temporal characterization phase (2026-07-22):** No production code moved
  or changed. Focused end-to-end tests now pin the two real coastdown date
  header layouts, millisecond-preserving run datetimes, elapsed and legacy time
  fallbacks, malformed temporal fields, inclusive 300-second matching, stable
  nearest/tie/duplicate selection, time-only and midnight behavior, concrete
  `AGRICULTR_SPLIT.csv` values, and traceability through correction and the
  comparison pair. Two current ambiguities remain deliberately unchanged:
  two-field `HH:MM` run text is consumed as elapsed `MM:SS`, and automatic
  fallback can match a different-date record solely by time of day. Exact sync
  fields remain in the calculated pair and calculation audit UI, while the
  current workbook exposes only their environmental summary.
- **Temporal-phase validation:** The 9 focused temporal checks, 85-test loader,
  weather, correction, sample-data, and AppTest matrix, and 436-test full suite
  pass, as do Ruff, compile, Streamlit startup, and diff hygiene.
- **Fourth narrow phase (2026-07-22):** Per-run `Start Time` normalization,
  elapsed/absolute classification, legacy clock fallbacks, naive datetime
  construction, and debug messages moved unchanged into the private
  `_parse_coastdown_start_time` helper. File-date discovery remains before the
  Pandas read, preserving its format priority and error order. Direct tests pin
  exact return types, milliseconds, malformed/missing values, the current
  two-field `HH:MM`-as-`MM:SS` behavior, and debug text without repeating
  synchronization coverage.
- **Fourth-phase validation:** The focused helper plus 10 temporal tests,
  86-test loader/weather/correction/sample/AppTest matrix, and 437-test full
  suite pass, as do scoped Ruff, compile, Streamlit startup, and diff checks.
  Broad Ruff reports only the same eight inherited `data/loaders.py` findings
  recorded before this extraction; no new finding is introduced.
- **Post-refactor review (2026-07-22):** The main function now orchestrates
  file/date discovery, table validation, enabled-run filtering, interval-column
  discovery, interval measurement extraction, Standard/Split output adaptation,
  diagnostics, and exception translation. The completed helpers reduced its
  Ruff profile from complexity 69, 84 branches, and 325 statements to 52, 61,
  and 233, but the remaining function is still not cohesive enough to close the
  finding. That review selected the neutral line-1/line-3 test-date discovery
  into `_parse_coastdown_test_header(lines, debug_output)` as the next boundary,
  returning `test_date` and `test_start_datetime` while leaving the caller's
  missing-date debug write and exception point unchanged. Fixed row 15, forced
  comma parsing, unsupported semicolon tables, naive datetimes, `HH:MM` as
  elapsed `MM:SS`, inactive `is_alta`, Standard/Split outputs, and all weather
  synchronization behavior remain intentional compatibility contracts. The
  70-test focused loader matrix, 437-test full suite, and diff hygiene pass.
- **Fifth narrow phase (2026-07-22):** The selected two-pass line-3/line-1
  header-date discovery moved into `_parse_coastdown_test_header` without
  changing delimiter selection, accepted formats, diagnostics, returned
  `date`/naive `datetime` values, or the caller's missing-date debug write and
  exception. Six focused tests cover four- and two-digit line-3 dates, comma
  and semicolon metadata, line-1 date/minute/second fallbacks, both-pass order,
  malformed headers, and isolated unexpected failures. The public loader now
  measures complexity 33, 35 branches, and 150 statements; the extracted
  compatibility helper measures 22, 28, and 94. Finding 13 remained In Progress
  at this checkpoint until a separate post-extraction cohesion review decided
  whether further movement would clarify ownership or only fragment the loader.
- **Fifth-phase validation:** The 76-test focused loader suite and 443-test full
  suite pass. Ruff reports only the same eight inherited `data/loaders.py`
  findings, with none in the new tests; compile, Streamlit startup, and diff
  hygiene pass.
- **Final reassessment (2026-07-22):** The remaining 33-complexity,
  35-branch, 150-statement function is a cohesive loader pipeline: filter
  enabled runs, locate interval columns, collect interval measurements, and
  adapt that shared result to Split or legacy Standard output. Extracting the
  column scan would pass tightly coupled frame/header/debug state into another
  function, while extracting the output branch would isolate only a small
  representation choice. Both would move complexity without clarifying
  ownership. No further high-value extraction is justified.
- **Status:** Completed

### 14. Stale state keys obscure the canonical Split model

- **Severity:** Low
- **Confidence:** Medium-High
- **Locations:** `app.py` state initialization, snapshot, and reset loops;
  calculation and page state readers.
- **Evidence:** Active code writes or initializes `weather_data_split`,
  `data_info`, `mass_input_mode`, `split_source_files`,
  `split_ambient_version`, `excel_buffer`, and `split_processed_at` without an
  active read that affects current Split behavior. `using_split_method` and
  `test_method` are read only by legacy pages. Split export uses
  `split_results_excel_cache`, and traceability uses `split_input_sources`.
- **Why it is a problem:** Persisted state is larger and harder to reason about,
  while similarly named obsolete and canonical fields invite incorrect reads.
- **Risk:** Medium because dynamic loops, widget management, and saved states can
  hide compatibility dependencies.
- **Recommended action:** Deprecate and remove one key per patch. Add explicit
  snapshot migration or compatibility reads where old saved tests require them.
- **Validation:** Round-trip save/load/reset/edit operations across old and new
  state shapes and inspect every page after each key removal.
- **First low-risk batch (2026-07-22):** New tests no longer initialize,
  persist, or write `mass_input_mode` and `split_source_files`. Legacy snapshots
  retain those fields in their stored dictionaries, while live state ignores
  them and continues from canonical `vehicle_info`/`total_mass` and
  `split_input_sources`.
- **Second low-risk batch (2026-07-22):** Active Split initialization, builders,
  and persistence no longer write `data_info`; old snapshots retain it without
  restoring it to live state. `split_processed_at` remains persisted because it
  is observable processing metadata with no canonical timestamp replacement.
- **Scoped retention batch (2026-07-22):** `weather_data_split` remains for
  legacy weather reads, `excel_buffer` for the legacy visible download, and
  `split_ambient_version`/`split_processed_at` for observable invalidation and
  processing metadata. Malformed legacy ambient versions now recover only when
  a real ambient mutation records the next version; valid counters are unchanged.
- **Final legacy-method batch (2026-07-22):** The active Split workflow no
  longer initializes, writes, restores, or persists `using_split_method` or
  `test_method`; explicit Split navigation is the canonical method identity.
  Old snapshots retain both fields without promoting them into live state.
  Unrouted legacy pages resolve only exact historical values through a
  page-private compatibility helper, default malformed or absent values to
  Split, and keep direct method selection outside persisted test state.
- **Validation result:** Focused state, routing, persistence, direct legacy-page,
  and AppTest regressions cover single-key, dual-key, malformed, switching,
  round-trip, canonical-routing, and idempotent-load cases. The 407-test full
  suite, scoped Ruff, compile validation, Streamlit startup, and diff hygiene
  pass.
- **Status:** Completed

### 15. Project documentation no longer matches ownership

- **Severity:** Low
- **Confidence:** High
- **Locations:** `CLAUDE.md:59-62`; `tasks/todo.md:271-274`;
  `docs/split_auto_selection_plan.md`.
- **Evidence:** The structure documentation names pages that do not exist.
  `tasks/todo.md` attributes Excel generation to the Results page although
  `data/split_exporters.py` owns it, and still lists moving the exporter after
  that move. The automatic-selection plan combines early future-state text with
  later implemented rounds.
- **Why it is a problem:** Future cleanup can follow obsolete ownership
  information and incorrectly classify live code as legacy.
- **Risk:** Very low if edits remain targeted and historical decisions are not
  rewritten.
- **Recommended action:** Correct current file ownership and mark superseded plan
  sections as historical. Preserve durable lessons.
- **Validation:** Check every documented path and owner against the current
  import graph.
- **Resolution (2026-07-21):** `AGENTS.md` and `CLAUDE.md` now name the active
  Split pages and current parser, weather, result, and workbook owners.
  Implemented export and automatic-selection tracker items are closed; obsolete
  milestones and round-local limitations remain available but are explicitly
  historical or superseded. The automatic-selection plan now separates current
  behavior, deferred work, and its implementation history. The independent
  coefficient-sign conflict remained assigned to finding 19 at that checkpoint;
  finding 19 was resolved separately on 2026-07-23.
- **Validation result:** Repository-wide stale-name and ownership searches found
  only explicitly historical, legacy, removed, or intentionally nonexistent
  references. Documented active paths were checked against the import graph;
  Markdown fences and local links are balanced/valid, non-document hashes are
  unchanged, and `git diff --check` passes.
- **Status:** Completed

## Test Coverage Gaps

### 16. Critical Streamlit orchestration is untested

- **Severity:** High
- **Confidence:** High
- **Locations:** `app.py`; `tests/`.
- **Evidence:** The audit found no test importing or executing the top-level
  app workflow. New, edit, save, load, reset, and multi-test state flows were
  not exercised. Focused orchestration tests now cover creation, rename-only
  editing, legacy and canonical reopening, active-test switching, state
  isolation, incomplete snapshots, and results routing through `AppTest`.
- **Why it is a problem:** Findings 2, 3, 10, 11, and 14 can regress without any
  current test failure.
- **Risk:** Low to add focused tests; high if state cleanup proceeds first.
- **Recommended action:** Add the smallest behavioral Streamlit `AppTest` or
  mocked workflow checks needed for new-test creation and state persistence
  before changing session keys or tab execution.
- **Validation:** Run the workflow checks against both clean state and a legacy
  persisted snapshot.
- **Status:** Completed. Added behavioral helper-level coverage plus one real
  `AppTest` workflow without refactoring application code.

### 17. Several tests enforce source text rather than behavior

- **Severity:** Low
- **Confidence:** High
- **Locations:** `tests/`, especially page and architecture tests using
  `inspect.getsource`; duplicated candidate-set validation cases in
  `test_split_auto_selection.py` and the dedicated candidate-set validation
  test module.
- **Evidence:** The initial inventory found eighteen source-inspection tests:
  ten repeated Streamlit-independence checks and eight page tests asserting
  literal source fragments, widget keys, or progress constants. The first batch
  converted three page tests to rendered-output checks. The second batch
  consolidated five architecture checks into one runtime import-boundary test.
  The final batch converted or consolidated the remaining ten cases. A
  repository-wide search now finds zero `inspect.getsource` cases. The final
  public-validator regression reports missing F0/F2 as diagnostic-only while
  the render-path test limits the UI to the two normative time constraints.
- **Why it is a problem:** Safe refactors fail tests despite unchanged behavior,
  while orchestration bugs can pass because the page is never executed.
- **Risk:** Medium if assertions are deleted before equivalent behavioral or
  dependency-boundary checks exist.
- **Recommended action:** Keep one clear architecture rule for Streamlit
  independence, replace page-source assertions with interaction tests, and
  remove only exact duplicate validator cases.
- **Validation:** Deliberately rename an internal helper or reformat a page and
  confirm behavioral tests remain stable while an actual workflow regression
  still fails.
- **Status:** Completed. Missing coefficients are behaviorally reported without
  becoming normative failures, and the localized render path exposes no
  coefficient-based constraint.

#### Inventory and classification (2026-07-21)

| Test | Brittle dependency | Class | Decision |
|---|---|---:|---|
| `test_split_auto_selection.py::test_module_does_not_import_streamlit` | `inspect.getsource` for two modules | 4 | Consolidated in the final batch into the runtime import-boundary test. |
| `test_split_candidate_generation.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in batch two into the runtime import-boundary test. |
| `test_split_candidate_set_validation.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in batch two into the runtime import-boundary test. |
| `test_split_comparison_merge.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in batch two into the runtime import-boundary test. |
| `test_split_deviation_analysis.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in the final batch into the same import-boundary test. |
| `test_split_pair_candidate.py::test_module_does_not_depend_on_streamlit` | `inspect.getsource` | 4 | Consolidated in the final batch into the same import-boundary test. |
| `test_split_selection_algorithms.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in the final batch into the same import-boundary test. |
| `test_split_time_validation.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in batch two into the runtime import-boundary test. |
| `test_split_vehicle_mass.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in batch two into the runtime import-boundary test. |
| `test_split_weather_context.py::test_module_does_not_import_streamlit` | `inspect.getsource` | 4 | Consolidated in the final batch into the same import-boundary test. |
| `test_render_has_only_two_default_enabled_time_constraint_checkboxes` | widget-key fragments and nearby `value=True` text | 2 | Replaced in the final batch with an isolated render-path test. |
| `test_render_exposes_advanced_v2_search_controls` | widget keys and call-argument fragments | 2 | Consolidated into the same render-path test. |
| `test_search_diagnostic_exposes_v2_strategy_and_counts` | renderer translation-key fragments | 1 | Replaced now with emitted metric values and limit-warning behavior. |
| `test_progress_reserves_completion_for_after_constrained_search` | exact progress constants and statement order | 2 | Consolidated into the final render-path test. |
| `test_normative_constraint_diagnostic_omits_coefficient_cv` | absence of coefficient field names in source | 1 | Replaced now with the rendered six-row time diagnostic. |
| `test_generation_diagnostics_show_counts_and_prefilter_per_group` | metadata and translation-key fragments | 1 | Replaced now with emitted counts, status, and table values. |
| `test_selection_diagnostics_wraps_generation_and_search_in_one_expander` | helper names and expander source | 2 | Removed after both parent rendering paths gained semantic output coverage. |
| `test_execution_result_and_fallback_offer_use_selection_diagnostics` | helper-name fragments | 2 | Replaced with direct behavioral coverage of both rendering paths. |
| `test_candidate_set_validation_keeps_f0_cv_as_diagnostic` | duplicated validator case | 3 | Remove later after strengthening the dedicated case. |
| `test_candidate_set_validation_keeps_f2_cv_as_diagnostic` | duplicated validator case | 3 | Remove later after strengthening the dedicated case. |
| `test_candidate_set_validation_fails_time_group_cv` | duplicated validator case | 3 | Remove later; the dedicated test covers the same check. |
| `test_high_coefficient_cv_is_diagnostic_when_times_pass` | duplicate destination | 4 | Consolidate the separate F0/F2 assertions here later. |
| `test_time_group_cv_remains_normative_failure` | duplicate destination | 4 | Keep as the dedicated time-group failure case after consolidation. |

Classifications: 1 = replace now; 2 = keep temporarily; 3 = remove because
equivalent behavioral coverage exists; 4 = consolidate duplicated coverage.

#### First-batch behavioral replacements

| Converted test | Old assertion | New behavior | Equivalence |
|---|---|---|---|
| Search diagnostics | Renderer source contained five translation keys. | Calling the renderer emits all V2 counts/status values and the limit warning. | Stronger: it verifies actual Streamlit output without depending on labels or widget order. |
| Normative constraint diagnostic | Renderer source omitted `cv_f0_pct` and `cv_f2_pct`. | Coefficient data is supplied, but the rendered table contains exactly the six normative time values. | Stronger: it proves coefficient diagnostics do not leak into the visible normative table. |
| Generation diagnostics | Renderer source contained count, prefilter, and table field names. | Calling the renderer emits generated/failed totals, enabled status, and per-group input/output/filtered counts. | Stronger: it verifies the user-visible projection rather than implementation spelling. |

#### Second-batch architecture replacements

| Selected test | Old source-level assertion | New observable behavior | Equivalence or strength | Duplicate removed |
|---|---|---|---|---|
| Candidate generation module boundary | Source omitted Streamlit imports and `st`. | A fresh process imports the module while `streamlit` is unavailable. | Stronger: direct and indirect runtime dependencies fail without depending on source spelling. | Yes; folded into the shared boundary test. |
| Candidate-set validation module boundary | Source omitted Streamlit imports. | A fresh process imports the module while `streamlit` is unavailable. | Stronger: it validates the executable dependency boundary. | Yes; folded into the shared boundary test. |
| Comparison-merge module boundary | Source omitted Streamlit imports and `st`. | A fresh process imports the module while `streamlit` is unavailable. | Stronger: aliases and indirect imports are covered. | Yes; folded into the shared boundary test. |
| Time-validation module boundary | Source omitted Streamlit imports and `st`. | A fresh process imports the module while `streamlit` is unavailable. | Stronger: harmless formatting no longer matters, but a real dependency fails. | Yes; folded into the shared boundary test. |
| Vehicle-mass module boundary | Source omitted the word `streamlit`. | A fresh process imports the module while `streamlit` is unavailable. | Stronger: comments and identifiers no longer fail the test; runtime coupling does. | Yes; folded into the shared boundary test. |

#### Final-batch replacements (remaining ten cases)

| Test or guarantee | Previous source-level assertion | Replacement behavior | Why equivalent or stronger | Duplicate removed |
|---|---|---|---|---|
| Auto-selection and candidate-set module boundary | Both module sources omitted Streamlit imports and `st`. | Each named module imports in its own fresh process while Streamlit is unavailable. | Direct and indirect runtime coupling now fails; candidate-set remains independently covered without a second source scan. | Yes; consolidated into the shared boundary test. |
| Default time constraints | Two widget-key fragments had nearby `value=True`, and a coefficient key was absent. | The rendered constraint group is asserted to contain exactly the two translated time constraints, both enabled, and both values reach the orchestrator. | Stronger: missing coefficients are separately reported by the public validator without adding a normative UI constraint. | Consolidated with the advanced-settings render test. |
| Advanced V2 search controls | Three widget keys and three argument fragments appeared in source. | The rendered translated controls accept distinct values and the orchestrator receives those exact values. | It proves user input reaches execution, which source presence could not establish. | Consolidated with the default-constraints render test. |
| Progress completion | Source contained exact progress constants and placed `1.0` before a later statement. | During an executed render, all phase updates stay incomplete and completion is emitted only after the orchestrator returns; translated phase captions are observed. | It preserves the visible completion contract without locking internal percentages or statement order. | Consolidated with the render execution test. |
| Diagnostics wrapper | Source named one expander and two private helpers. | Both parent rendering paths emit translated generation metrics, prefilter status, and the search-not-applicable caption. | Semantic output remains covered; expander state, Markdown styling, and private call structure are not contracts. | Yes; the standalone wrapper-layout test was removed. |
| Execution-result and fallback diagnostics | Both function sources named the private diagnostics helper. | Direct invocation of each renderer emits the same translated diagnostic semantics. | It proves both paths expose diagnostics rather than merely containing a call fragment. | Consolidated into one subtested behavioral case. |
| Deviation-analysis module boundary | Source omitted Streamlit imports and `st`. | The named module imports in a fresh process while Streamlit is unavailable. | Runtime dependency isolation is stronger and formatting-independent. | Yes; consolidated into the shared boundary test. |
| Pair-candidate module boundary | Source omitted Streamlit imports and `st`. | The named module imports in a fresh process while Streamlit is unavailable. | Runtime dependency isolation is stronger and formatting-independent. | Yes; consolidated into the shared boundary test. |
| Selection-algorithms module boundary | Source omitted Streamlit imports and `st`. | The named module imports in a fresh process while Streamlit is unavailable. | Runtime dependency isolation is stronger and formatting-independent. | Yes; consolidated into the shared boundary test. |
| Weather-context module boundary | Source omitted Streamlit imports. | The named module imports in a fresh process while Streamlit is unavailable. | Runtime dependency isolation is stronger and also catches indirect imports. | Yes; consolidated into the shared boundary test. |

## Risky Findings Requiring Manual Validation

### 18. Inherited Standard pages and dependency island removed

- **Severity:** Medium
- **Confidence:** High on internal routing, imports, persisted state, exports,
  and tests. The undocumented direct-import and blank-URL compatibility
  contract was explicitly retired in Batch 2.
- **Current locations:** Seven Python modules remain under `pages/`:
  `__init__.py`, Vehicle Data, and the five active `page_split_*` modules. No
  inherited Standard page remains.
- **Correction to the initial audit:** The earlier location list named
  `page_3_analise_individual.py`, `page_4_comparacao.py`,
  `page_5_resultados.py`, and `page_6_resultados_finais.py`; those files do not
  exist in the current tree. The first inventory found five inherited page
  files totaling 4,922 lines plus the 53-line compatibility helper.
- **Batch 1 result (2026-07-23):** Removed `page_5_comparativo.py` (544 lines)
  and `page_6_resultados.py` (541 lines). Their only helper,
  `utils/pair_time_analysis.py` (178 lines), had no package export, test,
  dynamic import, or remaining code caller after those deletions and was
  removed too. Batch 1 deleted 1,263 production lines and changed no tests.
- **Batch 2 result (2026-07-23):** Removed `_page_1_obsoleto.py` (299 lines),
  `page_3_analise_pares.py` (2,241 lines),
  `page_4_selecao_algoritmo.py` (1,297 lines), and their private 53-line
  `_legacy_method_state.py` helper. Outside that four-file island, the only
  code consumers were three direct-import compatibility tests, which were
  retired. Active stale-snapshot state and AppTest routing coverage remain.
- **Batch 3 result (2026-07-23):** Removed the now-closed Standard dependency
  island: `core/corrections.py`, `data/exporters.py`, obsolete coefficient and
  correction adapters from `core/calculations.py`, legacy weather adapters
  from `data/loaders.py`, their lazy package exports, the exclusive corrected-
  pair compatibility test, and translation keys owned only by the retired
  pages. The active `calcular_energia()` kernel and
  `carregar_dados_csv_robusto()` loader retain unchanged behavior.

#### Route model

- `app.py:1719-1776` is the active Split router. It conditionally imports and
  renders exactly five main tabs: Vehicle Data, Interval Selection, Pair
  Analysis, Final Comparison, and Split Results.
- Pair Analysis imports `page_split_auto_selection.py` only when its nested
  Automatic Selection tab is open.
- There are no `st.navigation`, `st.switch_page`, or `st.page_link` calls in
  the repository route flow.
- Streamlit 1.57's legacy pages-directory manager registers every
  `pages/*.py` except dotfiles and `__init__.py`. A leading underscore is not
  excluded. `.streamlit/config.toml` sets `showSidebarNavigation=false`, which
  hides the generated navigation but leaves those page paths registered.
- Batch 2 removes the four inherited blank paths without changing
  `app.render_test_analysis()` or any active tab identifier.
- Every page file only defines functions at top level; none calls `render()`.
  Direct execution therefore imports the module but renders a blank page.

#### Page/module inventory

`Persisted` below means the business-state keys are in `app.TEST_STATE_KEYS`;
widget/tab/cache keys remain session-local unless noted.

| Module | Primary classification | Registered/imported by | Session-state and snapshot compatibility | Tests importing it directly |
|---|---|---|---|---|
| `pages/__init__.py` | Imported dependency | Python package initialization only; excluded from Streamlit page discovery | No state | None |
| `pages/page_2_dados_veiculo.py` | Actively routed | Main tab 1 in `app.render_test_analysis()` | Uses persisted `data_loaded`, `vehicle_info`, `total_mass`, vehicle widget values, and completion state. `app.load_test_state()` supplies canonical defaults and old vehicle-widget fallbacks. | `test_app_orchestration.py`, `test_split_tab_routing.py` |
| `pages/page_split_auto_selection.py` | Actively routed nested page | Imported by `page_split_coefficient_calculation.py` for nested tab 3 | Uses persisted parsed runs, interval config, mass/vehicle/weather, comparison pairs, pending selection, replacement request/dialog state, and last result. Error and widget keys are transient. | `test_split_auto_selection_page.py`, `test_split_tab_routing.py` |
| `pages/page_split_coefficient_calculation.py` | Actively routed | Main tab 3 in `app.render_test_analysis()`; imports Automatic Selection | Uses persisted parsed/input/ambient/mass/weather/result/comparison state. Tab, graph-selection, legacy-final marker, and some caches are transient compatibility/UI state. | `test_split_comparison.py`, `test_split_display.py`, `test_split_final_state_migration.py`, `test_split_tab_routing.py`, `test_weather_sync.py` |
| `pages/page_split_final_comparison.py` | Actively routed | Main tab 4 in `app.render_test_analysis()` | `split_comparison_pairs` is persisted and canonical. Deviation cache, checkbox keys, and `navigate_to_results` are derived/transient. | `test_split_comparison.py`, `test_split_final_comparison_performance.py`, `test_split_final_comparison_visual.py`, `test_split_final_state_migration.py`, `test_split_tab_routing.py` |
| `pages/page_split_results.py` | Actively routed | Main tab 5 in `app.render_test_analysis()` | Reads persisted comparison, mass, and vehicle state. Deviation/export caches are derived. `core.split_state` explicitly handles aggregate-only legacy Split final summaries without treating Standard page-6 state as canonical. | `test_split_comparison.py`, `test_split_final_state_migration.py`, `test_split_results_formatting.py`, `test_split_tab_routing.py` |
| `pages/page_split_workflow.py` | Actively routed | Main tab 2 in `app.render_test_analysis()` | Uses persisted source, interval draft/config, parse-dirty/issues, loaded-data, and vehicle-completion state. Tab widget state is transient. | `test_split_tab_routing.py` |

Every remaining page module is an active routed page or its package
initializer. No test-only or dead page module remains.

#### Shared-helper boundary

- No inherited page helper remains under `pages/`.
- `data.loaders.carregar_dados_csv_robusto` must remain: `app.py` and Split
  parser characterization tests still use it. Removing the obsolete page-1
  caller does not make the loader dead.
- `core.calculations.calcular_energia` remains because active
  `core/split_energy.py` deliberately delegates to the neutral kernel.
- `core/corrections.py` and `data/exporters.py` had no caller after the page
  removals; their lazy exports and compatibility-only tests were part of the
  same closed Standard contract and were retired in Batch 3.
- `read_weather_station_csv` and `find_closest_weather_record` had no remaining
  caller after pages 1, 3, and 4 were removed. Active weather loading and
  synchronization remain owned by `data/weather_loader.py` and Split modules.
- `utils/pair_time_analysis.py` was removed after pages 5 and 6 because the
  final repository-wide caller check found no remaining code caller.
- **Remaining problem:** None within finding 18. The separately tracked mixed
  responsibility inside the retained shared coastdown loader is not a legacy
  page dependency.
- **Risk:** Low. Active Split owners, state compatibility, formulas, routing,
  weather loading, and workbook export remain independently covered.

#### Safest cleanup plan

1. **Batch 1 — completed 2026-07-23:** Deleted `page_5_comparativo.py`,
   `page_6_resultados.py`, and conclusively unreferenced
   `utils/pair_time_analysis.py`. No test referenced any target, so no test
   edit was necessary. `data/exporters.py` was retained until its separate
   public compatibility contract was audited in Batch 3.
2. **Batch 2 — completed 2026-07-23:** Deleted
   `_page_1_obsoleto.py`, `page_3_analise_pares.py`,
   `page_4_selecao_algoritmo.py`, and `_legacy_method_state.py` together.
   Retired only their three direct-import compatibility tests. Kept the active
   tests proving old method flags remain stored but never enter live Split
   state or override canonical routing.
3. **Batch 3 — completed 2026-07-23:** Removed only the unreferenced Standard
   adapters, modules, lazy exports, exclusive tests, and page-owned translation
   families. Preserved `carregar_dados_csv_robusto` and `calcular_energia`
   because active Split code still uses them.

**Must remain:** all five `page_split_*` modules,
`page_2_dados_veiculo.py`, `pages/__init__.py`, the shared coastdown loader,
the neutral energy kernel, and all Split-owned calculation, weather, parser,
state, and export modules.

- **Inventory validation (2026-07-23):** Before Batch 1, direct
  `AppTest.from_file()` execution of all 13 page modules completed with zero
  Streamlit exceptions and zero titles/headers, confirming importable blank
  scripts.
- **Batch 1 validation (2026-07-23):** Direct AppTests load all 11 remaining
  page modules without exceptions. The 28 focused orchestration, routing, and
  package-import tests and the 443-test full suite pass. All 81 remaining
  Python files compile, and scoped Ruff over active routing, tests, and
  remaining utilities passes. Repository-wide Ruff reports 22 pre-existing
  findings only in explicitly untouched calculations, Standard exports,
  loader code, and retained legacy pages 1, 3, and 4. Focused AppTest processes
  emitted post-success Windows temporary-directory permission warnings without
  changing their zero exit status.
- **Batch 2 validation (2026-07-23):** Direct AppTests load all seven remaining
  page modules without exceptions. The 25 focused orchestration, routing, and
  package-import tests and the 440-test full suite pass. All 77 remaining
  Python files compile, and scoped Ruff over active routing, tests, pages, and
  utilities passes. Repository-wide Ruff now reports only nine pre-existing
  findings in explicitly untouched `core/calculations.py`,
  `data/exporters.py`, and `data/loaders.py`.
- **Batch 3 validation (2026-07-23):** Direct AppTests load `app.py` and all
  seven remaining page modules without exceptions. The 70 focused routing,
  package, energy, loader, and weather tests and the 435-test full suite pass.
  All 74 Python files compile. Scoped Ruff over `core`, `data`, tests, and
  translations passes; repository-wide Ruff reports only five unchanged E402
  findings in `app.py`. `git diff --check` passes.
- **Status:** Completed — all three batches are complete and no inherited
  Standard page dependency remains.

### 19. Split coefficient sign guidance aligned to canonical code

- **Severity:** High
- **Confidence:** High
- **Obsolete evidence (before resolution):** `AGENTS.md`, `CLAUDE.md`, and
  `docs/calculations.txt` showed signs opposite to the deliberate,
  test-locked road-load-positive implementation.
- **Resolution (2026-07-23):** Treated `core/split_calculations.py` as
  canonical and corrected only conflicting guidance. Positive `Delta V` feeds
  `f0 = a1*V2^2 - a2*V1^2` and `f2 = a2 - a1`; guidance now forbids sign
  inversion and display-time `abs()`. No production formula or output changed.
- **Full-flow evidence:** `split eliezer high.csv` and
  `split eliezer low.csv` reproduce `F0 = 139.4112` and `F2 = 0.646178`.
  Correction, comparison, Results consolidation, and workbook export preserve
  positive coefficients.
- **Validation:** 62 focused tests, 13 sample-data tests, and the 435-test full
  suite passed. All 74 Python files compile, scoped Ruff and diff checks pass.
- **Status:** Completed

### 20. Orphan translations and stale compatibility text removed

- **Severity:** Low
- **Confidence:** High
- **Locations:** `translations.py`; `core/split_display.py:157`
  (`format_split_pair_public_label`); legacy input, vehicle-mass, wind, and
  selector aliases.
- **Initial audit evidence:** Before finding 18 Batch 3, 755 translation keys
  included 506 active exact references, 88 legacy-only exact references, and
  161 without an exact reference. Batch 3 removed 121 keys whose ownership by
  the retired pages was independently proven; dynamic f-string key families
  still prevent treating every remaining unmatched key as dead.
  `format_split_pair_public_label` has no internal caller but is explicitly a
  compatibility alias. Similar compatibility surfaces exist for old input
  layouts, vehicle mass names, wind names, and the v1 selector wrapper.
- **Finding 20 result (2026-07-23):** Removed 148 keys (592 lines) with neither
  an active literal owner nor a live dynamic-family owner. The remaining 487
  keys comprise 469 with literal source evidence and 18 reached through the
  bounded dynamic input-mode, meteo-method, deviation-status, and result-status
  families. Empty translation section labels, the obsolete pages 2-6 comment,
  the README's pre-removal ownership text, and present-tense references to the
  retired page 4 were removed or corrected. No test was tied exclusively to the
  deleted text.
- **Retained compatibility:** Persisted Split summary, input-layout,
  vehicle-mass, and weather aliases remain active. The module-level
  `format_split_pair_public_label` alias and selector compatibility wrapper were
  retained because removing them would change a public compatibility surface,
  outside this text-only cleanup.
- **Why it is a problem:** Bulk deletion based on a single text search can break
  dynamic translations, persisted data, or external consumers.
- **Risk:** High for bulk removal; low when keys are removed with a proven dead
  owning workflow.
- **Recommended action:** Keep dynamic translation families explicit during
  future audits and remove compatibility APIs only in a separately authorized
  export/persisted-state migration.
- **Validation:** 106 focused translation/UI tests, 8 active AppTests, the
  435-test full suite, compile of 74 Python files, scoped Ruff, and diff checks
  passed. Repository-wide Ruff still reports only the five unchanged `app.py`
  E402 findings caused by the existing path bootstrap.
- **Status:** Completed

## Confirmed Indirect Usage

These items initially looked unused in ordinary static searches. They are
recorded to prevent unsafe deletion.

### 21. Automatic-selection page is indirectly rendered

- **Severity:** Informational
- **Confidence:** High
- **Location:** `pages/page_split_coefficient_calculation.py:1702,1717`;
  `pages/page_split_auto_selection.py`.
- **Evidence:** The automatic-selection page is absent from the top-level app tab
  list but is imported and rendered inside the coefficient-calculation page.
- **Risk:** Removing it breaks automatic selection.
- **Recommended action:** Preserve it; document the nested ownership if the page
  structure is reorganized.
- **Validation:** Open the coefficient page and execute automatic selection.
- **Resolution:** Confirmed as an active nested Split page and preserved.
- **Status:** Completed — preserve

### 22. Package initializers execute through submodule imports

- **Severity:** Informational
- **Confidence:** High
- **Locations:** `core/__init__.py`; `data/__init__.py`.
- **Evidence:** Python executes a package initializer before loading
  `core.split_*` or `data.loaders`, even when no caller explicitly imports the
  initializer.
- **Risk:** Deleting initializer imports without tracing re-export consumers can
  break imports; leaving them preserves unwanted legacy coupling.
- **Recommended action:** Treat this as the prerequisite for finding 12, not as
  dead code.
- **Validation:** Import submodules and package-level aliases separately.
- **Resolution:** Finding 12 replaced eager exports with lazy package lookup
  while preserving package initialization and supported aliases.
- **Status:** Completed — preserve

### 23. Session and widget keys have dynamic references

- **Severity:** Informational
- **Confidence:** High
- **Locations:** `app.py:583-606`; generic state snapshot/reset helpers;
  Streamlit widgets; parse-feedback configuration dictionaries.
- **Evidence:** `TEST_STATE_KEYS`, defaults, widget keys, and
  `split_parse_feedback_current/processed` fields are accessed through loops,
  dictionaries, or Streamlit's automatic widget state rather than explicit
  attribute reads.
- **Risk:** A naive unused-state deletion can break snapshots, resets, or widget
  persistence.
- **Recommended action:** Preserve dynamically referenced keys unless a
  lifecycle trace and migration test prove them obsolete.
- **Validation:** Exercise initialize, edit, save, load, reset, and widget
  callback paths.
- **Resolution:** Dynamic state consumers were retained and covered during the
  canonical-state and stale-key findings.
- **Status:** Completed — preserve

### 24. Plotly is dynamically imported and required

- **Severity:** Informational
- **Confidence:** High
- **Locations:** `pages/page_split_coefficient_calculation.py:1350,1404`;
  graph tests; `requirements.txt`.
- **Evidence:** Plotly imports occur inside graph-rendering functions and tests,
  so a top-level import scan can incorrectly classify the dependency as unused.
- **Risk:** Removing it breaks calculated-pair graphs at runtime.
- **Recommended action:** Preserve Plotly.
- **Validation:** Render both graph paths in a clean environment.
- **Resolution:** Plotly remains an active runtime dependency for both graph
  paths and was preserved.
- **Status:** Completed — preserve

### 25. Sample datasets have test and validation roles

- **Severity:** Informational
- **Confidence:** High
- **Locations:** `sample_data/Split`; `sample_data/Standard`; integration tests;
  `tasks/todo.md`.
- **Evidence:** Split samples are referenced by integration tests. Standard
  samples are explicitly retained in task tracking for comparative validation,
  even when not part of active Split routing.
- **Risk:** Removing them weakens regression and manual validation coverage.
- **Recommended action:** Preserve them until the tracked validation work is
  complete; remove only with an explicit replacement fixture/data decision.
- **Validation:** Map every sample to its automated or manual validation case.
- **Resolution:** Split samples remain active integration fixtures; Standard
  samples remain separate comparative loader fixtures.
- **Status:** Completed — preserve

### 26. Compatibility aliases may serve persisted or external consumers

- **Severity:** Informational
- **Confidence:** Medium-High
- **Locations:** `core/split_display.py:157`; legacy input layout adapters;
  vehicle mass aliases; wind aliases; selector-v1 wrapper; loader parameters
  such as `is_alta`.
- **Evidence:** Some aliases have no active internal caller but are named or
  documented as compatibility surfaces, appear in tests, or accept data from
  previous application versions.
- **Risk:** Removing them can break saved data or callers outside the repository.
- **Recommended action:** Preserve them until an explicit compatibility window,
  consumer inventory, and persisted-state migration are defined.
- **Validation:** Load representative old files and saved states and check known
  external import/use documentation.
- **Resolution:** Proven persisted/public aliases remain compatibility
  contracts; only aliases conclusively owned by the retired Standard workflow
  were removed in findings 18 and 20.
- **Status:** Completed — preserve

## Staged Cleanup Plan

Each phase is intended to be a small, independently reviewable patch. Domain
equations and validation behavior are excluded unless a separate normative
review explicitly authorizes them.

1. **Mechanical removals:** Remove verified unused imports/constants, private
   dead helpers, the PyQt configuration module, SciPy, and Matplotlib. Correct
   stale documentation in the same documentation-only phase or separately.
2. **Parser side effect:** Remove unconditional debug-file writes and add the
   read-only/concurrency parser check.
3. **Runtime contract and workflow state:** Raise the Streamlit minimum, correct
   fixed-condition key mapping, and add focused app workflow coverage. Assess
   lazy tabs only after hidden-tab side effects are characterized.
4. **User-visible correctness:** Make final UI/export status use normative time
   validation and make export cache identity cover workbook traceability.
5. **State and tests:** Replace brittle page-source tests with behavior checks,
   then retire stale session keys one at a time with persisted-state migration.
6. **Import and duplication cleanup:** Reduce eager package exports and
   consolidate corrected-pair logic behind temporary compatibility aliases.
7. **Loader boundaries:** Characterize current behavior, then separate neutral
   file I/O from explicit Standard and Split adapters without changing parser
   results.
8. **Manual compatibility and normative review:** Validate direct routes, legacy
   files, translations, external imports, old saved data, and one independent
   ABNT calculation before deleting inherited Standard surfaces or reconciling
   formula documentation.

Immediate, well-supported cleanup is estimated at approximately 350-450 lines
plus two dependencies. After compatibility and normative validation, the
inherited legacy reduction opportunity is approximately 6,500 lines. These are
estimates, not deletion targets.

## Audit Validation Results

### Unit tests

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
```

Result:

```text
Ran 354 tests in 13.892s
OK
```

The first sandboxed run produced 14 `PermissionError` failures while tests
attempted to use the system temporary directory. Re-running the same suite with
the required filesystem permission passed completely. These were environmental
failures, not application assertions.

### Ruff

Command:

```text
ruff check --no-cache --select F401,F811,F821,F841 .
```

Result: 30 unused-name/import findings, mostly in inherited legacy modules. The
notable active findings were:

- unused `APP_RELEASE_DATE` import in `app.py`;
- unused `evaluate_split_constraint_satisfaction` import in
  `core/split_auto_selection.py`;
- unused `validate_split_candidate_set` import in
  `core/split_auto_selection.py`.

A complexity scan additionally identified
`data/loaders.py:carregar_dados_csv_robusto` at complexity 69, with 84 branches
and 325 statements. Complex domain-selection functions were not classified as
cleanup candidates based on complexity alone.

### Repository state

The audit intentionally changed no tracked files. Running the tests updated the
ignored `debug_vbox_date.txt`, which is evidence for finding 5. At audit
completion, `git status` and `git diff` were clean. This report is the only file
created after the audit.

## Assumptions

- Repository-wide static references are not proof that an API has no external
  consumer.
- Streamlit page discovery, widget state, callbacks, dynamic imports, package
  initializers, persisted test state, and translation-key construction were
  treated as indirect dependency mechanisms.
- Existing Split formulas, effective mass handling, climate correction, energy
  calculations, and validation thresholds are preserved until separately
  validated against an authoritative reference.
- Compatibility aliases and Standard reference data remain until their
  consumers and migration requirements are proven absent.
