# Ponytail Repository Audit - 2026-07-20

## Scope

This is a documentation-only audit of the Coastdown MDA Split repository. It
focuses on dead and duplicated code, inherited Standard-method paths, Streamlit
state and navigation, compatibility surfaces, maintainability, and test gaps.
No application code, tests, formulas, validation rules, or domain behavior were
changed as part of the audit.

Findings are ordered by risk within each section. A `Pending` status means the
finding has been documented but no cleanup or behavior change has been applied.

## Summary

| # | Title | Severity | Confidence | Recommended phase | Current status |
|---:|---|---|---|---|---|
| 1 | Split final status still uses non-normative coefficient variation | High | High | 4 | Completed |
| 2 | Fixed-condition inputs are ignored for new tests | High | High | 3 | Pending |
| 3 | Declared Streamlit minimum is incompatible with active API use | High | High | 3 | Completed |
| 4 | Export cache signature omits workbook-visible traceability | Medium | High | 4 | Completed |
| 5 | Successful parsing always writes a shared debug file | Medium | High | 2 | Completed |
| 6 | Unreferenced local functions remain in active modules | Low | High | 1 | Completed |
| 7 | Unused imports, constants, and dependencies | Low | High | 1 | Completed |
| 8 | Orphan desktop-GUI configuration module | Low | High | 1 | Completed |
| 9 | Duplicate corrected-pair implementation | Low | High | 6 | Pending |
| 10 | Main and nested tabs compute hidden content eagerly | Medium | High | 3 | Pending |
| 11 | Redundant derived session state | Low | Medium-High | 5 | Pending |
| 12 | Eager package initializers couple Split imports to legacy modules | Medium | High | 6 | Pending |
| 13 | Loader has mixed Standard/Split responsibility and extreme complexity | Medium | High | 7 | Pending |
| 14 | Stale state keys obscure the canonical Split model | Low | Medium-High | 5 | Pending |
| 15 | Project documentation no longer matches ownership | Low | High | 1 | Pending |
| 16 | Critical Streamlit orchestration is untested | High | High | 3 | Completed |
| 17 | Several tests enforce source text rather than behavior | Low | High | 5 | Pending |
| 18 | Large inherited Standard surface is isolated but route-discoverable | Medium | High | 8 | Pending |
| 19 | Split coefficient sign convention conflicts across repository guidance | High | High conflict / Low resolution | 8 | Pending |
| 20 | Translation and compatibility cleanup cannot rely on static counts | Low | High | 8 | Pending |
| 21 | Automatic-selection page is indirectly rendered | Informational | High | Preserve | Pending |
| 22 | Package initializers execute through submodule imports | Informational | High | Phase 6 prerequisite | Pending |
| 23 | Session and widget keys have dynamic references | Informational | High | Preserve | Pending |
| 24 | Plotly is dynamically imported and required | Informational | High | Preserve | Pending |
| 25 | Sample datasets have test and validation roles | Informational | High | Preserve | Pending |
| 26 | Compatibility aliases may serve persisted or external consumers | Informational | Medium-High | Phase 8 prerequisite | Pending |

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
- **Status:** Pending

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
- **Locations:** `core/calculations.py`
  (`calculate_single_pair_corrected_data`);
  `core/corrections.py` (`calculate_single_pair_corrected_data2`).
- **Evidence:** The functions contain duplicate corrected-pair behavior under
  different names and modules. Legacy callers still reference the older
  calculation surface.
- **Why it is a problem:** Fixes can diverge between two nominally equivalent
  paths, and the names do not establish which implementation owns the behavior.
- **Risk:** Medium because the legacy path and possible external imports may
  depend on the current symbols.
- **Recommended action:** Keep one implementation and make the other symbol a
  thin, documented compatibility alias during a migration period.
- **Validation:** Before consolidation, characterize both functions with the
  same representative inputs and assert identical outputs and errors.
- **Status:** Pending

### 10. Main and nested tabs compute hidden content eagerly

- **Severity:** Medium
- **Confidence:** High
- **Locations:** `app.py:1726-1755`;
  `pages/page_split_coefficient_calculation.py:1705-1717`.
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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Evidence:** Eighteen tests inspect source code. Ten enforce that pure modules
  do not import Streamlit, while eight assert literal page strings, widget keys,
  or progress constants. Some validator scenarios are covered both through the
  orchestrator file and its dedicated unit tests.
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
- **Status:** Pending

## Risky Findings Requiring Manual Validation

### 18. Large inherited Standard surface is isolated but route-discoverable

- **Severity:** Medium
- **Confidence:** High that it is outside the active Split workflow; Medium on
  removal safety
- **Locations:** `pages/_page_1_obsoleto.py`,
  `pages/page_3_analise_individual.py`,
  `pages/page_4_comparacao.py`, `pages/page_5_resultados.py`,
  `pages/page_6_resultados_finais.py`, `utils/pair_time_analysis.py`,
  `data/exporters.py`, `core/corrections.py`, `config.py`,
  `.streamlit/config.toml:17`.
- **Evidence:** These inherited files total approximately 6,259 lines and are
  not called by the active Split tabs. However, Streamlit automatically
  discovers Python files under `pages/`. `showSidebarNavigation=false` hides
  navigation but does not prove direct routes are unavailable. The page modules
  currently define render functions without invoking them at top level, so
  direct routes are expected to be blank rather than useful.
- **Why it is a problem:** Standard code remains within the Split application's
  route and import surface, increasing confusion and the risk of accidental
  reuse.
- **Risk:** High. Project tracking explicitly retains some Standard assets for
  compatibility and validation; saved states or external links may also exist.
- **Recommended action:** Inventory direct URLs, external scripts, persisted
  states, and required Standard reference data. Move non-page components out of
  `pages/` or adopt explicit navigation before deleting any inherited files.
- **Validation:** Exercise every known legacy route, open representative old
  saved tests, and run export/import compatibility checks.
- **Status:** Pending

### 19. Split coefficient sign convention conflicts across repository guidance

- **Severity:** High
- **Confidence:** High that the conflict exists; Low on which source must change
- **Locations:** `AGENTS.md:151-166`; `CLAUDE.md:128-130`;
  `docs/calculations.txt`; `core/split_calculations.py:103-109`;
  `tasks/lessons.md:350-359`; calculation tests and examples.
- **Evidence:** AGENTS and CLAUDE describe positive `Delta V` with
  `f0 = a2*V1^2 - a1*V2^2` and `f2 = a1 - a2`. The implementation, examples,
  lessons, and tests use the opposite signs to produce positive road-load
  coefficients. The implemented behavior is deliberate and test-locked.
- **Why it is a problem:** Maintainers following repository instructions can
  "correct" working code to the opposite convention, or reports can document a
  formula different from the calculation.
- **Risk:** Critical. Equations and domain behavior must not change during
  cleanup.
- **Recommended action:** Independently reproduce one authoritative ABNT
  reference case, obtain domain sign-off, and then reconcile documentation or
  implementation in a dedicated normative change.
- **Validation:** Compare hand calculation, independent spreadsheet, current
  implementation, and expected report signs for the same reference inputs.
- **Status:** Pending

### 20. Translation and compatibility cleanup cannot rely on static counts

- **Severity:** Low
- **Confidence:** High
- **Locations:** `translations.py`; `core/split_display.py:157`
  (`format_split_pair_public_label`); legacy input, vehicle-mass, wind, and
  selector aliases.
- **Evidence:** Of 755 translation keys, 506 have active exact references, 88
  have legacy-only exact references, and 161 have no exact reference. Dynamic
  f-string key families prevent treating the last group as dead.
  `format_split_pair_public_label` has no internal caller but is explicitly a
  compatibility alias. Similar compatibility surfaces exist for old input
  layouts, vehicle mass names, wind names, and the v1 selector wrapper.
- **Why it is a problem:** Bulk deletion based on a single text search can break
  dynamic translations, persisted data, or external consumers.
- **Risk:** High for bulk removal; low when keys are removed with a proven dead
  owning workflow.
- **Recommended action:** Delete translation families only alongside their
  removed pages/features. Keep compatibility aliases until an external and
  persisted-state migration inventory proves them unnecessary.
- **Validation:** Render every locale and workflow, scan for missing-key output,
  and load old persisted inputs before and after each removal.
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
- **Status:** Pending

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
