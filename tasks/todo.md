## Phase 1 - Project setup
- [x] Rename visible app identity from Standard to Split
- [x] Review inherited Standard pages
- [x] Identify pages to keep, remove, or rewrite
- [x] Create Split-specific project structure
- [x] Create initial Split parser module
- [x] Create initial Split calculation module

## Phase 2 - Split parser
- [x] Support separate high/low files
- [x] Support combined file with both intervals
- [x] Support full coastdown file with dynamic interval extraction
- [x] Add interval configuration UI
- [x] Add configurable coastdown interval step (`step_kmh`, default 5 km/h)
- [x] Require exact parser bins from start/end/step and block incompatible spans
- [x] Remove Split loader assumptions that high starts at 90, low at 45 and bins always step by 5 km/h
- [x] Preserve labeled VBOX interval columns and report expected/found/missing bins
- [x] Use explicit high/low role plus current config for unlabeled separate files; block unlabeled combined files
- [x] Track file/run/column traceability
- [x] Enforce source role: high slot only high, low slot only low
- [x] Require complete interval coverage before accepting high/low
- [x] Store `content_sha256` in `split_input_sources`
- [x] Use explicit `split_input_mode` from UI: `separate` or `combined`
- [ ] Validate parser with more real combined/full coastdown files

## Phase 3 - Split calculations
- [x] Centralize the normative Split mass chain: M = running-order mass + 136 kg, me = informed value or 3% of M, and Me = M + me.
- [x] Make manual and automatic Split calculations consume the same normalized effective mass.
- [x] Add compatibility normalization for legacy `total_mass` / `effective_mass` sessions without adding 136 kg twice.
- [x] Implement Delta V positive interval convention
- [x] Implement f'0 and f'2 calculation helper
- [x] Add validation rules
- [x] Validate sign convention
- [x] Test with synthetic examples
- [x] Test with real separate high/low files
- [x] Document positive Delta V vs signed normative deceleration convention
- [x] Isolate pure Split climatic correction from f'0/f'2 to F0/F2
- [x] Keep corrected F0/F2 separate from uncorrected f'0/f'2
- [x] Save explicit per-direction and pair-mean coefficient keys in every Split result
- [ ] Validate Split climatic-correction constants and formula against the normative reference
- [ ] Confirm final unit wording and normative notation for report/export

## Phase 4 - UI workflow
- [x] Adapt vehicle data page
- [x] Create Split file loading/parser review page
- [x] Create Split analysis/calculation page
- [x] Create Split validation behavior for incomplete high/low inputs
- [x] Create Split results page
- [x] Rename Split workflow tab to Interval Selection
- [x] Add placeholder Coefficient Calculation tab
- [x] Replace simple high/low selection with complete ida/volta pair selection in Coefficient Calculation
- [x] Calculate and save complete Split pairs from high+, low+, high- and low-
- [x] Add final comparison table for calculated Split pairs
- [x] Add collapsible cards for comparison pairs
- [x] Organize each comparison card into ambient, corrected coefficients, CV and energy columns
- [x] Show ida/volta CV for corrected F0/F2 and warn above 10%
- [x] Add remove pair and clear comparison actions
- [x] Add separate input slots for high-speed, low-speed and meteo files
- [x] Allow replacing/removing high, low and meteo inputs separately
- [x] Invalidate Split-derived state when files change
- [x] Invalidate Split-derived state when input mode changes
- [x] Show Split input mode message based on parsed high/low records
- [x] Show upload slots from explicit mode: separate high/low or single combined
- [x] Invalidate and reparse Split state when interval start/end/reference/step changes
- [ ] Manual UX test for replacing only high, only low and only meteo in an existing test
- [ ] Manual UX test for switching input mode in an existing test
- [x] Move high/low pair selection and coefficient calculation logic from Interval Selection to Coefficient Calculation
- [x] Add final comparative table/cards for multiple calculated Split pairs
- [x] Implement pure Split energy calculation from corrected F0/F2 with an explicit inherited cycle profile
- [ ] Review remaining hardcoded English strings in Split workflow/results for i18n

## Phase 5 - Export and reporting
- [x] Show and export explicit running-order, test, rotational-equivalent and effective masses with numeric Excel values.
- [x] Adapt basic Excel export for Split
- [x] Include parser traceability
- [x] Include calculation inputs and outputs
- [x] Include validation warnings
- [x] Include weather/meteo inputs and synchronization audit in the Split workbook owned by `data/split_exporters.py`.
- [ ] Decide final normative report layout and units wording
- [ ] Manually validate the complete mass workflow in the running Streamlit app, including manual calculation, automatic selection, Results and downloaded Excel.

## Migration implementation status
- [x] Quarantine visible Standard workflow from main navigation
- [x] Rename visible app identity to Split
- [x] Add Split-specific parser module
- [x] Add Split-specific coefficient calculation module
- [x] Add Split workflow and results pages
- [x] Add basic Split Excel export
- [x] Validate parser with real separate high/low files
- [x] Add tests for positive Delta V, invalid Delta t, invalid mass, invalid V2/V1 and configurable intervals
- [x] Add tests for real Split high/low sample import
- [x] Add tests preventing high-only from becoming false low and low-only from becoming false high
- [x] Add test that same filename with different content is parsed from actual content, not reused by name
- [ ] Validate parser with real combined/full coastdown files
- [ ] Decide final normative report layout and units wording

## Current operational tracker - 2026-06-09
- [x] Split file input roles implemented: high-speed, low-speed and meteo have distinct slots.
- [x] Edit/replace/remove flow implemented for high, low and meteo files.
- [x] CSV replacement clears `split_parsed_runs`, `split_results`, `split_final_results`, `excel_buffer` and increments `split_input_version`.
- [x] Meteo replacement/removal clears derived final/export state and resets time-only sync.
- [x] Parser blocks incomplete high/low combinations instead of generating partial or position-based intervals.
- [x] Input mode is explicit in the UI and saved as `split_input_mode`.
- [x] Main Split navigation now has Vehicle Data, Interval Selection, Coefficient Calculation, Final Comparison and Split Results.
- [x] Rename the third Split navigation tab to `3. Análise de Pares`.
- [x] Organize Pair Analysis into Coefficient Calculation and Graphical Analysis sub-tabs.
- [x] Keep the existing coefficient-selection, correction, energy, meteo and comparison persistence flow unchanged inside the calculation sub-tab.
- [x] Add Split-only run filters by high/low interval and +/- direction using clean public run labels.
- [x] Add Plotly speed-versus-elapsed-time and Delta t charts from processed Split runs.
- [x] Add calculated-pair visualization from the four records stored in `split_comparison_pairs`.
- [x] Add explicit empty and aggregate-data states to Graphical Analysis.
- [x] Split Graphical Analysis into independent High speed and Low speed sections.
- [x] Give each graphical section its own direction filter, selected-run state, Add all and Clear selection actions.
- [x] Reconcile each section selection against its current direction filter without changing the other section.
- [x] Apply a Standard-inspired dark Plotly theme to Split speed curves, highlight active pair components in high/low charts and keep graph trace labels compact.
- [x] Simplify Graphical Analysis labels and hovers to run plus Delta t only, remove filenames from speed/Delta t charts and hide the calculated-pair visualization section.
- [ ] Run a manual UI regression of Graphical Analysis with real separate high/low files and a saved complete pair.
- [ ] Manually confirm High speed Add/Clear actions do not change Low speed selection, and vice versa.
- [x] Coefficient Calculation tab manually selects high+, low+, high- and low- before calculating.
- [x] Coefficient Calculation tab calculates direction +, direction - and arithmetic pair average.
- [x] Coefficient Calculation supports fixed or synchronized ambient conditions.
- [x] Coefficient Calculation stores corrected direction +, direction - and pair-average F0/F2.
- [x] `split_results` and `split_comparison_pairs` share canonical `f0_prime_*`, `f2_prime_*`, `F0_*` and `F2_*` keys.
- [x] Calculation summary, comparison table/cards and Split Results read the same canonical coefficient keys with legacy fallback.
- [x] Keep the latest calculated coefficient summary visible after Streamlit reruns.
- [x] Ambient mode, fixed temperature or fixed pressure changes invalidate calculated results and comparison cards.
- [x] Coefficient Calculation tab can add complete ida/volta pairs to `split_comparison_pairs`.
- [x] Move the complete comparison table/cards out of Coefficient Calculation into `page_split_final_comparison.py`.
- [x] Final Comparison uses the Standard page as a visual template: batch actions, compact column rows, per-row selection/removal and source colors.
- [x] Comparison table includes four runs, corrected F0/F2, energy, directional ambient conditions and warning status.
- [x] Manual pairs store `selection_source="manual"`; automatic suggestions use the same table contract with `selection_source="algorithm"`.
- [x] Add persistent pair selection and compact remove/clear controls without Standard selection state.
- [x] Comparison cards show directional meteo sync data and identify the conditions used by climatic correction.
- [x] Split Results consolidates only pairs marked `selected` in `split_comparison_pairs`.
- [x] Split Results shows corrected F0/F2, energy, final CVs, validation status, selected-pair table and per-pair traceability.
- [x] Split Results handles empty comparison, no selection, missing corrected coefficients, missing energy and meteo warnings without traceback.
- [x] Final Split consolidation is isolated in pure helpers under `core/split_results.py` with focused unit tests.
- [x] Replace technical `split_pair_*` labels in Split tables, cards, expanders and selectors with public high/low run composition.
- [x] Simplify coefficient-calculation run options to `Run | dt | filename`, keeping direction and timestamps in traceability sections.
- [x] Add regression coverage for the actual coefficient `selectbox` formatter and public pair columns.
- [x] Clean the Coefficient Calculation visual flow: collapse the selected-pair technical summary, keep meteo sync details in one closed expander, remove loose ambient text after coefficient results and show compact `split_comparison_pairs` preview cards.
- [x] Replace the calculated-result summary with Split-specific HTML tables for uncorrected and corrected coefficients, including CV and wind threshold highlights, and remove the selected-pair technical summary from the calculation UI.
- [x] Move the calculated coefficient HTML tables into a closed details expander while keeping the pair result title and add-to-comparison action visible.
- [x] Diagnose and restart duplicate Streamlit servers on ports 8501/8502 that predated the display changes.
- [x] Refactor Final Comparison first stage around `split_comparison_pairs`: Split-only selection helpers, batch actions, corrected/reference tables and per-row removal.
- [x] Separate corrected Split pairs from uncorrected reference pairs; only corrected pairs can be selected for final results.
- [x] Add regression coverage for Split comparison normalization, corrected-pair detection, N/A formatting, CV warning threshold, public labels and clear-all state scope.
- [x] Add Final Comparison selected-pair statistics from `core/split_results.py`, keeping F0/F2/energy means and CVs aligned with Split Results.
- [x] Add Final Comparison action to calculate/navigate to Split Results through `navigate_to_results`, without Standard final-result state.
- [x] Add selected-pair traceability expander using existing Split comparison fields; defer Delta T conformity analysis for Split.
- [x] Fix Final Comparison checkbox state handling so widget keys are not modified after `st.checkbox` is instantiated.
- [x] Rework Final Comparison Split rows to closer Standard-style `st.columns` + compact HTML cells, with red CV warnings and orange reference rows.
- [x] Add Final Comparison visual legend and selected-row highlighting for corrected Split pairs.
- [x] Align Final Comparison table cells with fixed 50px height, full-width flex cells and centered row controls.
- [x] Stack Split Final Comparison ambient ida/volta values and standardize table coefficients to F0 `.2f` and F2 `.4f`.
- [x] Adapt `data/split_exporters.py` to the selected-pair consolidation contract and restore explicit export generation in Split Results.
- [ ] Run manual regression in the app before first commit: create test, replace high, replace low, remove low, replace meteo, remove meteo.
- [ ] Run manual regression with one high-only CSV and confirm calculation remains blocked with friendly warning.
- [ ] Run manual regression with one low-only CSV and confirm calculation remains blocked with friendly warning.
- [ ] Run manual regression with high+low CSVs and confirm final f'0/f'2 match expected values.
- [ ] Run manual regression with four selected runs and confirm ida, volta and pair-average f'0/f'2.
- [ ] Run manual regression with explicit combined mode and confirm high-only/low-only combined files block calculation.
- [ ] Run manual regression with a real VBOX file configured with a non-5 km/h interval step.
- [ ] Confirm whether production combined VBOX exports include explicit speed-bin labels.

## Meteo status
- [x] Weather CSV loader remains neutral infrastructure reused by Split.
- [x] Weather file can be added, replaced and removed from the Split test editor.
- [x] Meteo replacement/removal invalidates stale final/export state.
- [x] Add neutral CSV/XLSX weather loader with normalized datetime, temperature, pressure, wind speed and wind direction.
- [x] Add pure weather synchronization with full-datetime preference, configurable maximum delta and audited time-only fallback.
- [x] Synchronize high+, low+, high- and low- independently in Coefficient Calculation.
- [x] Preserve canonical `ambient_by_component` traceability for high+, low+, high- and low- in calculated results and comparison pairs.
- [x] Calculate correction conditions as explicit high/low means per direction, preserving each source value and zero wind.
- [x] Audit Split wind loading: preserve literal zero, keep missing/invalid values as `None`, and reject unknown units.
- [x] Normalize declared wind units to m/s, including explicit km/h conversion with warning.
- [x] Validate `AGRICULTR_SPLIT.csv`: `Wind Speed` is declared in m/s and all 9,476 records contain literal zero.
- [x] Coefficient comparison cards show per-component sync method, timestamps, delta, weather values and warnings.
- [x] Preserve coastdown Start Time milliseconds in parsed run timestamps.
- [ ] Decide how declared coastdown timezone should be mapped when the weather file has no timezone metadata.
- [x] Apply isolated climatic correction from f'0/f'2 to F0/F2 using fixed or synchronized conditions.
- [ ] Complete normative validation of `Kt`, `Kp`, reference conditions and F2 unit conversion for Split.
- [x] Add all four `ambient_by_component` records to Split Results and the Split workbook.

## Energy status
- [x] Energy is calculated from corrected `F0_mean/F2_mean` and shown in Split results and comparison surfaces.
- [x] `core/split_energy.py` delegates explicitly to `core.calculations.calcular_energia(F0_mean, F2_mean)`.
- [x] Save the inherited formula origin as `standard_formula_calcular_energia` with unit `MJ/km`.
- [x] Save `energy=None` only when corrected F0/F2 are unavailable.
- [x] Save calculated `energy`, `energy_unit`, `energy_profile`, `energy_origin` and `energy_status` in results and comparison pairs.
- [x] Add tests for corrected-coefficient use, unavailable correction, comparison propagation and explicit units.
- [ ] Validate the provenance and normative applicability of the inherited city/highway constants and 55/45 weighting.

## Excel export status
- [x] Adapt Split Excel export to consume only pairs with explicit `selected=True` from `split_comparison_pairs` and corrected final F0/F2.
- [x] Restore the Split Results download after the exporter covers the new summary and all four component records.
- [x] Add the four component-level ambient records and weather sync audit to Excel.
- [x] Consolidate the final workbook into Resumo Final, Pares Selecionados and Análise de Desvios e Tempos.
- [x] Prevent technical `split_pair_*` ids from appearing as primary pair labels in the workbook.
- [x] Move vehicle and weather summaries into Resumo Final and keep per-pair weather in Pares Selecionados.
- [x] Remove the dedicated vehicle, times, weather and traceability sheets plus leave-one-out from Excel only.
- [x] Remove freeze panes and automatic filters from all three final workbook sheets.
- [x] Merge the four Resumo Final title rows across columns A:B and color the final-status cell by result.
- [x] Share the public pair-label helper between Excel and deviation analysis, including UI leave-one-out and weather rows.
- [x] Replace only the Pares Selecionados wide table with stacked IDA [+] and
  VOLTA [-] tables using grouped headers and one row per selected pair.
- [x] Export exact directional raw/corrected coefficients, energies calculated
  by the canonical helper, and high/low component weather without pair-level CVs.
- [x] Pass 36 focused workbook/sample/cache tests, scoped Ruff, compile and
  diff checks; full suite passed 452/453 with the already-tracked auto-selection
  radio-mock error.
- [x] Add Tempos de desaceleração with dynamic high/low subinterval columns,
  canonical run weather, pair-traceable selected order and Excel formatting.
- [x] Preserve exact processed subinterval `time_s` values in parsed records so
  the workbook never reconstructs them from totals or display values.
- [x] Verify exact subinterval-time preservation through calculated,
  comparison, selected and persisted pairs and the Excel cache signature.
- [x] Keep legacy pairs without `subinterval_times_s` unavailable and add one
  worksheet note requiring reprocessing instead of estimating from total time.
- [x] Pass 55 focused workbook/parser/cache/persistence tests and compile checks
  for the finalized subinterval-time path.
- [x] Pass 40 focused workbook/sample/cache tests, 22 interval-parser tests,
  compile, scoped Ruff and diff checks; full suite passed 456/457 with the
  already-tracked auto-selection radio-mock error.
- [ ] Manually validate the four-sheet workbook with real manual, fixed-weather and synchronized-weather pairs in Excel.
- [ ] Manually inspect the stacked Pares Selecionados headers and column widths
  in desktop Excel with multiple selected pairs.
- [ ] Manually inspect Tempos de desaceleração in desktop Excel with different
  high/low interval counts and repeated runs across selected pairs.

## Round 11A - Split Results and final Excel report
- [x] Refactor Split Results as a read-only executive summary based on Final Comparison selections.
- [x] Reuse `consolidate_split_final_results()` and `analyze_split_selected_deviations()` without UI formula duplication.
- [x] Show vehicle data, final F0/F2, CVs, energy, validation, selected-pair table, weather and traceability.
- [x] Create pure `data/split_exporters.py` without Streamlit imports.
- [x] Historical milestone (superseded): exported seven dedicated sheets before the workbook was consolidated into three sheets.
- [x] Add export tests for valid XLSX, sheets, selected-only filtering, missing values, weather alerts, immutability and Streamlit independence.
- [ ] Complete real-browser validation of selection refresh, page layout, download and Excel/UI value comparison.

## Known gaps and next steps
- [ ] Parser needs more real combined/full coastdown examples to validate heuristics beyond synthetic full-coastdown tests.
- [ ] Split workflow/results still contain English literal labels; convert important user-facing strings to `translations.py`.
- [x] Interval fields now edit a draft without automatically running parser validation on each Streamlit rerun.
- [x] Add explicit `Process Split intervals` action to validate, parse and commit interval configuration.
- [x] Mark processed data stale with `split_parse_dirty` after interval edits and block coefficient calculation until reprocessing.
- [x] Keep detailed missing-bin and validation feedback hidden until an explicit processing attempt.
- [x] Use stable per-test widget keys without dynamic `value`/`step` identity changes that caused lost number-input clicks.
- [x] Make Parser review consume an isolated snapshot of `split_interval_config` and `split_parsed_runs`, never the draft.
- [x] Record `split_processed_at` when a draft is explicitly promoted to processed configuration.
- [ ] Run manual regression for edit, stale-preview, processing-error and successful-reprocessing states.
- [ ] Review date/timezone policy for files with ambiguous dates or missing timezone metadata.
- [x] Add meteo synchronization details to the Split workbook without applying climatic correction implicitly.
- [ ] Continue visual polish after functional validation; keep technical meteo warnings collapsed by default.
- [ ] Validate the Final Comparison table manually with a larger number of pairs and narrow desktop widths.
- [ ] Manually recheck Final Comparison checkbox/batch/remove/results navigation with real browser state after the Streamlit session-state fix.
- [x] Add Split-specific Delta T conformity diagnostics for selected Final Comparison pairs by reusing `core/split_time_validation.py`.
- [x] Connect automatic Split selection to `selection_source="algorithm"` without importing the Standard algorithm workflow.
- [x] Audit the current manual Split pair calculation and comparison contracts before implementing automatic selection algorithms.
- [x] Extract a pure Split candidate-builder helper that reuses `calculate_complete_split_pair`, `apply_split_pair_correction` and `build_split_comparison_pair`.
- [x] Ensure automatic Split candidates enter `split_comparison_pairs` with `selection_source="algorithm"` and `selected=False`.
- [x] Add pure ranking and top-k selection helpers for automatic Split candidates.
- [x] Add pure normative time diagnostics for selected automatic Split candidates.
- [x] Add pure automatic-candidate enumeration from grouped Split runs without UI state.
- [x] Implement normative time/direction validation and constraint-first selection for generated automatic candidates.
- [x] Implement exact complete-candidate generation from grouped high+/low+/high-/low- Split runs.
- [x] Create a pure automatic-selection orchestrator combining exact generation, ranking, top-k and time diagnostics.
- [x] Create a pure merge helper for adding automatic candidates to `split_comparison_pairs` without selecting final results.
- [ ] Implement directional preselection for large Split candidate sets.
- [x] Implement controlled UI/sub-tab integration for exact automatic Split selection without auto-selecting final results.
- [x] Implement sub-tab Automatic Selection using `run_split_auto_selection_exact()` and `merge_algorithm_candidates_into_comparison_pairs()`.
- [x] Make Final Comparison row colors use `algorithm_sources`, `algorithm_source` and `selection_source`, with compatibility-flag fallback.
- [x] Initialize `split_comparison_pairs` only when absent so normal tab navigation preserves the existing list.
- [x] Expand each automatic suggestion into Ida, Volta and highlighted Media rows, keeping Energia as the final column.
- [x] Separate suggested candidates into individual titled blocks and display missing table values as `-`.
- [x] Keep automatic candidates pending until the user explicitly adds the current suggestion set to Final Comparison.
- [x] Add bounded energy/target replacement pools and pure conflict-aware pending-candidate replacement.
- [x] Add per-candidate Replace and pending-only Clear actions to the Automatic Selection UI.
- [x] Ensure replacement conflicts exclude the outgoing candidate and distinguish old/existing/repeated skips.
- [x] Show each suggested High/Low run with its component Delta t in the candidate tables.
- [x] Build a bounded balanced replacement reserve by scanning the full ranking for options useful to each visible position.
- [x] Add `st.dialog` preview, confirmation and cancellation before replacing a pending suggestion.
- [x] Make replacement preview and application share the pure `find_replacement_candidate()` contract and exact signature.
- [x] Diagnose failed replacement attempts with pool and skip counters.
- [x] Prevent replacement dialogs from reopening on unrelated reruns by separating request and open-state lifecycle.
- [x] Sanitize orphan replacement requests after dismiss, merge, invalidation or missing pending suggestions.
- [x] Integrate per-run weather synchronization into automatic Split generation and derive each candidate context from its four enriched runs.
- [x] Manually validate energy, target, replacement, duplicate merge, selected preservation and `max_combinations` behavior in the Automatic Selection sub-tab.
- [x] Decide and implement Split-specific visual colors for energy, target and combined suggestions.
- [ ] Keep `sample_data/Split/` and `sample_data/Standard/` separated as validation datasets for each method.

## Split/Standard separation audit - 2026-06-10
- [x] Confirm the main app navigation imports only Vehicle Data and Split pages.
- [x] Confirm active Split modules do not read `calculated_pairs`, `pares_finais_selecionados`, `algorithm_results`, `f0_corr` or `f2_corr`.
- [x] Confirm Standard pages 3-6 are outside the active Split navigation.
- [x] Finding 18: inventory every `pages/` module across active routing, hidden direct routes, imports, session-state/snapshot dependencies, and direct tests.
- [x] Finding 18: confirm active Split pages import no helper from inherited pages 1 or 3-6.
- [x] Finding 18 Batch 1: remove legacy `page_5_comparativo.py` and `page_6_resultados.py`; final caller check confirmed `utils/pair_time_analysis.py` was unreferenced, so remove it in the same batch.
- [x] Finding 18 Batch 2: retire pages 1, 3, and 4 with `_legacy_method_state.py`; remove only their direct-import compatibility tests while preserving active stale-snapshot and routing coverage.
- [x] Finding 18 Batch 3: remove the closed Standard correction/export dependency island, its lazy public exports and exclusive tests, obsolete loader weather adapters, and translations owned only by the retired pages.
- [x] Historical checkpoint (superseded): Split Excel was generated by the Results page rather than the Standard `data/exporters.py`.
- [x] Historical checkpoint (superseded by Batch 3): stop eager Standard imports while preserving their then-supported public compatibility through lazy exports.
- [ ] Split `data/loaders.py` into a neutral VBOX reader plus explicit Split and Standard adapters.
- [x] Move Split workbook generation into `data/split_exporters.py` as `export_split_final_results_to_excel`; keep `page_split_results.py` as the UI caller.
- [x] Reduce `core/calculations.py` to the neutral `calcular_energia(f0, f2)` kernel used by active Split energy calculation.
- [x] Remove the old coefficient/correction attempts from `core/calculations.py` after confirming no active or dynamic consumer imported them.
- [x] Remove `core/corrections.py` and `data/exporters.py` after their last page callers, lazy exports, and compatibility-only tests were retired in finding 18 Batch 3.
- [ ] Review the inherited 3% rotational-inertia default in Vehicle Data against the final Split normative workflow.
- [x] Update the stale `app.py` comment that described pages 2-6 compatibility as the current architecture.
- [x] Finding 20: classify all remaining translation keys by literal source,
  bounded dynamic family, persisted compatibility, or orphan ownership.
- [x] Finding 20: remove 148 orphan keys and stale translation section labels
  without changing active text, routing, calculations, exports, or UI behavior.
- [x] Finding 20: correct stale pages 2-6, README ownership, and retired page 4
  documentation while preserving supported Split compatibility surfaces.
- [x] Finding 20: pass 106 focused translation/UI tests, 8 active AppTests, the
  435-test full suite, compile of 74 Python files, scoped Ruff, and diff checks.
- [x] Finding 20 completed; repository-wide Ruff retains only the five existing
  `app.py` E402 findings from the path bootstrap.

## Round 12A - Weather synchronization in Automatic Selection
- [x] Synchronize weather once per high/low run without mutating `split_parsed_runs`.
- [x] Validate wind above 3 m/s, temperature above 35 °C and missing required weather; keep pressure traceability-only.
- [x] Preserve four weather components, aggregate summary, correction context and warnings in candidates and comparison merge.
- [x] Rank by explicitly preferred corrected energy/F0/F2 fields while preserving fixed-mode fallbacks.
- [x] Add optional invalid-weather filtering, enabled by default in synchronized UI mode.
- [x] Show synchronization counters and compact candidate weather summaries/details.
- [x] Add pure-module, synchronization, validation, candidate, ranking, filtering and merge tests.
- [ ] Complete the required real-app manual validation with high/low/weather files, both filter states, merge, deviation analysis and Split Results.

## Round 12B - Fixed environmental parameters and weather consistency
- [x] Add per-test fixed temperature and pressure inputs to Automatic Selection.
- [x] Build a canonical fixed correction context with `user_fixed_inputs` traceability.
- [x] Preserve fixed `environmental_conditions` and `weather_summary` without false missing-weather status.
- [x] Keep hot fixed candidates with a temperature warning and no missing-wind rejection.
- [x] Standardize new wind fields on `wind_speed_mps` while retaining legacy read aliases.
- [x] Centralize environmental reads used by deviation analysis, Split Results and Split Excel export.
- [x] Confirm climatic correction consumes pressure in kPa without conversion.
- [ ] Complete real-app manual validation for edited fixed inputs, cards, comparison, deviations, results/export and synchronized-mode regression.

## Performance and visual-unit standardization
- [x] Replace eager Final Comparison tabs with conditional section rendering.
- [x] Keep the Table section limited to persisted pair display and selection updates.
- [x] Cache deviation analysis by a stable signature of selected analysis inputs.
- [x] Invalidate deviation and Excel caches when final selection changes.
- [x] Generate Split Excel only after an explicit Generate Excel action and reuse it by signature.
- [x] Remove repeated units from Split Results metric and table values.
- [x] Keep workbook units in headers and quantitative cells numeric.
- [x] Add behavioral tests for lazy rendering, cache reuse/invalidation, on-demand export and unit formatting.
- [x] Vectorize weather timestamp parsing while preserving scalar parsing rules and exact Split fixture records.
- [x] Replace per-candidate Target-ranking deep copies with top-level copies while preserving ranking and input immutability.
- [x] Normalize weather records once per Split synchronization batch and use a single-pass nearest-record lookup.
- [x] Throttle automatic-selection progress callbacks to displayed integer-percentage changes.
- [x] Precompute each automatic-selection high/low directional result once per batch and reuse it across opposite-direction combinations.
- [x] Document automatic-selection constraints and safely expand only the search pool and evaluated-set defaults.
- [ ] Complete real-browser performance comparison and visual/export validation.

## Round 10A - Final Comparison deviation analysis
- [x] Preserve the existing Final Comparison behavior in the `Tabela` sub-tab.
- [x] Analyze only pairs explicitly stored with `selected=True`.
- [x] Add pure F0/F2 sample CV, per-pair deviation and leave-one-out diagnostics.
- [x] Reuse Split time validation for the four deltaT groups and opposite-direction means.
- [x] Add configurable diagnostic alerts for wind above 3 m/s and temperature above 35 °C; pressure remains display-only.
- [x] Add PT/EN labels and unit coverage for the pure analysis module.
- [ ] Complete the required real-browser manual regression for both sub-tabs, selection persistence, weather alerts and Split Results navigation.

## Normative Split time-label audit - 2026-06-23
- [x] Confirm independent sample C.V. checks for high+, high-, low+ and low- with the 2.5% limit.
- [x] Confirm separate opposite-direction mean checks for high and low with the 10% limit.
- [x] Confirm one-sample C.V. remains inconclusive and does not fail automatically.
- [x] Centralize public Δt labels and include configured high/low reference speeds.
- [x] Apply the public labels in Final Comparison, Split Results and the final Excel workbook.
- [x] Add pure-helper, normative-limit, UI-projection and Excel regression tests.
- [ ] Manually validate the four C.V. rows, two opposite-direction rows and generated Excel in a real Streamlit session with multiple selected pairs.

## Round 13A.1 - Normative candidate-set validation
- [x] Add a pure candidate-set validator for corrected F0/F2 sample CV, four Delta t group CVs and two opposite-direction mean differences.
- [x] Keep one-pair and missing-sample checks inconclusive without automatic rejection.
- [x] Add ranked constrained top-k search with early `run_usage` pruning and a configurable evaluation limit.
- [x] Return the best ranked failed set only as an explicit, unapplied fallback in metadata.
- [x] Add focused tests for every normative failure, non-top-k valid selection, repeated runs, fallback and evaluation limit.
- [x] Integrate the constrained selector into the automatic-selection orchestrator and UI in Round 13A.2.

## Round 13A.2 - Candidate-set validation in Automatic Selection UI
- [x] Initially add three set criteria; superseded by the normative time-only adjustment below.
- [x] Route the orchestrator through constrained top-k only when at least one criterion is enabled.
- [x] Preserve the previous top-k flow when all set criteria are disabled.
- [x] Store approved or inconclusive suggestions in pending with constraint validation metadata.
- [x] Keep failed constrained results outside pending and expose the best failed set as an explicit fallback offer.
- [x] Promote fallback candidates to pending only after the user clicks the explicit confirmation button.
- [x] Show all eight coefficient/time diagnostic values and warnings for failed fallback sets.
- [x] Revalidate current and simulated sets in the replacement preview without blocking the existing replacement action.
- [x] Recompute and persist constraint status after a confirmed replacement.
- [x] Add PT/EN strings and automated core/page coverage for approved, failed, fallback, replacement and disabled-criteria flows.
- [ ] Complete the requested real-browser validation for Energy and Target, approved set, failed set, fallback, merge and Final Comparison deviation status.

## Round 13B.1 - Constraint-first automatic set selector
- [x] Audit the v1 constrained search pool, early return, ranking dependence and evaluation cap.
- [x] Add `constraint_first_v2` with default pool `max(200, k * 50, k + 100)` and 20,000 set evaluations.
- [x] Validate complete sets without partial CV/time pruning and preserve only safe `run_usage` pruning.
- [x] Continue searching after the first valid set and choose the minimum aggregate zero-based rank-index sum.
- [x] Deduplicate candidate identities before combinatorial search.
- [x] Track strategy, actual pool, evaluated/valid set counts, evaluation-limit status and best valid/failed scores.
- [x] Keep the original helper name as a compatibility wrapper and route the automatic-selection orchestrator through v2.
- [x] Add regression proving a valid set beyond the former top-100 prefix is found.
- [x] Add regression proving the best aggregate-score valid set wins instead of the first valid set.
- [x] Preserve explicit failed fallback, repeated-run protection and Streamlit independence.
- [x] Distinguish an exhaustive no-valid result from an incomplete search stopped by `max_set_evaluations` in Round 13B.2.

## Round 13B.2 - Constraint-first v2 diagnostics in Automatic Selection UI
- [x] Keep legacy top-k when all active set criteria are disabled and use v2 when any criterion is enabled.
- [x] Add collapsed advanced inputs for maximum search-pool size and evaluated-set limit.
- [x] Use defaults `max(200, k * 50, k + 100)` and 20,000 evaluations.
- [x] Pass both advanced limits through the pure automatic-selection orchestrator.
- [x] Show evaluated sets, valid sets, actual pool and `constraint-first` strategy for approved and failed searches.
- [x] Replace the absolute no-valid wording with a result scoped to the performed search.
- [x] Show a specific warning when `max_set_evaluations_reached=True` indicates an incomplete search.
- [x] Preserve explicit fallback confirmation, selector-v2 metadata and failed-set warnings in pending cards.
- [x] Offer the exact best failed K-set with its own measured normative diagnostics, pair cards, and explicit use/cancel actions.
- [x] Preserve current/after constraint diagnostics in replacement preview without blocking replacement.
- [x] Add PT/EN strings and automated coverage for defaults, advanced controls, metrics, limited-search wording, fallback and legacy top-k.
- [ ] Complete real-browser Energy/Target validation with approved, exhaustive-failed, limited-failed and fallback scenarios.

## Critical hotfix - Bounded constrained search performance
- [x] Diagnose the full generation progress reaching 100% before constrained set search completed.
- [x] Reduce default pool to `max(80, k * 20, k + 40)` and evaluated sets to 3,000.
- [x] Add a 30-second wall-clock limit using `time.perf_counter()`.
- [x] Make backtracking itself cooperatively stop on time/evaluation budgets, including branches that yield no complete set.
- [x] Return explicit top-k-compatible fallback metadata without applying pending automatically.
- [x] Add elapsed time, time limit and timeout status to selector metadata and UI diagnostics.
- [x] Add a configurable advanced maximum-search-time field.
- [x] Reserve 100% progress for completion and expose generation, ranking, constrained search and finalization phases.
- [x] Show a limited-search warning for timeout or evaluated-set exhaustion.
- [x] Confirm that set-signature caching would have no useful reuse because the deduplicated combination generator emits each set once.
- [x] Add timeout, evaluation cap, fallback, safe-default, phase and legacy-top-k regression coverage.
- [ ] Complete mandatory real-browser Energy/Target timing validation with default and increased budgets.

## Normative adjustment - Time-only automatic Split selection
- [x] Remove the `CV F0/F2 <= 10%` checkbox from Automatic Selection.
- [x] Keep only Delta t group CV <= 2.5% and opposite-direction mean difference <= 10% as active constraints.
- [x] Preserve F0/F2 sample CV and status as explicitly diagnostic-only fields in candidate-set validation.
- [x] Remove coefficient CV from `passed`, normative `failed_checks` and automatic-selection warnings.
- [x] Normalize selector, orchestrator, pending and replacement metadata to time-only constraint keys.
- [x] Ignore legacy `coefficient_cv` flags without activating constrained search or failing replacement status.
- [x] Remove F0/F2 rows from the normative failure diagnostic and label candidate-card F0/F2 CV as diagnostic.
- [x] Update failure messages and the six normative time-check labels.
- [x] Add regressions proving high F0/F2 CV is accepted when all time checks pass.
- [x] Preserve time-group and opposite-direction failures, fallback, timeout and legacy top-k behavior.
- [ ] Complete real-browser Energy/Target validation and confirm Final Comparison/Results keep coefficient CV separate from automatic normative filtering.

## MAD pre-filter - 2026-06-24
- [x] Add pure `filter_group_by_mad()` to `core/split_candidate_generation.py` with MAD outlier detection, min-pool-size guarantee, too-few-records and mad-is-zero skip reasons.
- [x] Apply the pre-filter per group (high_plus/low_plus/high_minus/low_minus) after `split_runs_by_role_and_heading()` and before the cartesian product in `generate_full_split_candidates_exact()`.
- [x] Add `use_mad_prefilter`, `mad_multiplier` and `mad_min_pool_size` parameters to `generate_full_split_candidates_exact()` and record per-group `prefilter` metadata.
- [x] Wire the same parameters through `run_split_auto_selection_exact()` in `core/split_auto_selection.py`, defaulting `mad_min_pool_size` to `max(k + 2, 4)`.
- [x] Add regression coverage for normal filtering, too-few-records skip, mad-is-zero skip, min-pool-size preservation, disabled prefilter and cartesian-size reduction.
- [ ] Validate real-world timing improvement on a 12-run-per-group dataset in the running Streamlit app.

## Run-uniqueness search fix - 2026-06-24
- [x] Diagnose the reported `evaluated_sets_count=0` failure (K=5, ~12 runs/group, pool=300, ~8s timeout) with a synthetic cartesian-product reproduction.
- [x] Confirm `_iter_candidate_sets()`'s run-uniqueness scope was already correct (tracks only the partial in-progress k-set, not the whole pool) — the originally suspected root cause did not match the reproduced behavior.
- [x] Identify the real causes: (1) the constrained search pool lacked enough distinct physical runs per Split component for a ranking that naturally clusters around the same few best runs, and (2) even with sufficient diversity, canonical rank-ordered backtracking can still stall deep in conflict-heavy branches before reaching a single complete leaf.
- [x] Add `min_run_diversity` to `_constraint_search_pool()` in `core/split_selection_algorithms.py`, expanding the pool past its base size until every component (high+/low+/high-/low-) has at least `max(3*k, k+10)` distinct physical runs (capped naturally by total distinct runs available).
- [x] Fix an off-by-one in the diversity tracking that counted a candidate's own identities before deciding whether to include it in the pool.
- [x] Add a bounded randomized rescue pass (`_randomized_disjoint_set()`) that only activates when the exhaustive search reaches its time/evaluation budget with `evaluated_sets_count == 0`, to recover a valid run-disjoint set when canonical traversal order stalls.
- [x] Add `pool_expanded_for_run_diversity`, `requested_pool_size` and `rescue` fields to selector metadata for full traceability.
- [x] Expose `generated_count`, generation `failed_count` and per-group MAD prefilter input/output/filtered counts in a new collapsed "Diagnóstico da seleção" expander in `pages/page_split_auto_selection.py`, shown for both the approved-result and fallback-offer paths.
- [x] Add regression coverage: realistic cartesian pool finds disjoint sets, final set never repeats a run, `avoid_repeated_runs=False` still bypasses uniqueness, MAD-prefiltered pipeline still finds disjoint sets, and the rescue pass activates/recovers only when DFS evaluates zero sets.
- [ ] Complete real-browser validation with a real ~12-run-per-group dataset and K=5 to confirm the previously reported timeout no longer occurs.

## Audit finding 3 - Streamlit minimum version - 2026-07-20

- [x] Trace active Split Streamlit APIs and their version floors.
- [x] Confirm launcher and validated environment versions remain compatible.
- [x] Raise the declared minimum to Streamlit 1.55.0.
- [x] Add structured dependency validation for the lower bound.
- [x] Run the complete validation matrix and update audit finding 3.

## Audit finding 1 - Split final conformity source - 2026-07-20

- [x] Trace the primary card, secondary banner, Excel status and compatibility
  field to their status sources.
- [x] Make both UI banners and Excel use `time_summary.passed`.
- [x] Preserve coefficient CV values/statuses with explicit diagnostic labels.
- [x] Keep legacy `conformity_status`, warnings and incomplete coefficient
  states separate from normative time conformity.
- [x] Cover all four time/coefficient outcomes and inconclusive time validation.
- [x] Run focused/full tests, workbook regression, Ruff, compile and diff checks.

## Audit finding 4 - Split export cache signature - 2026-07-20

- [x] Trace selected-pair fields through cache creation and workbook generation.
- [x] Replace the partial deviation signature with a deterministic snapshot of
  complete selected-pair export inputs.
- [x] Cover filename, run, subinterval, origin, correction, weather, missing
  values, NumPy scalars and dictionary ordering with focused regressions.
- [x] Confirm unchanged inputs preserve workbook bytes, layout and values.
- [x] Run focused and full regression suites, Ruff, compile and diff checks.

## Audit finding 5 - Shared VBOX debug file - 2026-07-20

- [x] Remove the unconditional `debug_vbox_date.txt` write from successful VBOX parsing.
- [x] Preserve date parsing, warnings, return values and existing error-path exception handling.
- [x] Add Windows-safe regressions for file creation, file preservation, denied writes, concurrency and expected parser outputs.
- [x] Run focused and full regression suites.

## Audit findings 6-8 - Low-risk cleanup - 2026-07-20

- [x] Trace private helpers, imports, constants, dependencies, `config.py`, and
  compatibility surfaces through runtime, tests, launchers, packaging, docs,
  callbacks, dynamic imports, and persisted state.
- [x] Remove the orphaned private helper cluster and its transitive imports.
- [x] Remove unused weather constants, SciPy, Matplotlib, and `config.py`.
- [x] Retain the public final-comparison helper and validator compatibility
  re-exports.
- [x] Pass the full suite, compile validation, scoped Ruff, dependency
  resolution, Streamlit startup smoke test, and diff check.

## Audit finding 9 - Corrected-pair consolidation - 2026-07-21

- [x] Inventory all four definitions, active callers, unused imports and
  package exports before editing.
- [x] Characterize the rich and raw-value contracts across correction,
  calculation and package import paths.
- [x] Preserve exact keys, types, numeric results, missing-value defaults and
  invalid-input exceptions.
- [x] Preserve module-specific runtime lookup of `calcular_energia` for both
  calculation compatibility paths without changing direct correction calls.
- [x] Keep the rich correction function canonical and replace the other three
  formula bodies with schema or compatibility adapters.
- [x] Pass focused/existing correction tests, the 370-test full suite, scoped
  Ruff, compile validation and diff checks.

## Audit finding 10 - Lazy tab rendering - 2026-07-22

- [x] Characterize every active main, pair-analysis and parser-review tab.
- [x] Render only the selected tab while preserving labels, keys and rerun state.
- [x] Run the legacy comparison-selection repair after pair mutations and before Results.
- [x] Cover selection switching, hidden-state isolation and incomplete saved state.
- [x] Pass focused/AppTest coverage, the 383-test full suite, Ruff, compile,
  Streamlit startup and diff checks.

## Audit finding 11 - Canonical final-result state - 2026-07-22

- [x] Inventory every `split_final_results` read, write, persistence path, and
  legacy saved-state shape before editing.
- [x] Make `split_comparison_pairs` canonical for current availability and
  selected-pair counts without changing calculations or exports.
- [x] Stop new redundant writes while retaining complete and aggregate-only
  legacy summaries during a documented migration window.
- [x] Migrate only complete legacy pair lists and explicitly report summaries
  that lack reconstructable pair data.
- [x] Require unique stable IDs, explicit selection, valid corrected fields,
  and agreement among all supplied legacy counts before migration.
- [x] Preserve aggregate-only summaries during passive ambient rendering and
  clear them only after a real invalidating mutation.
- [x] Cover canonical precedence, legacy migration, test switching, sidebar,
  Results, and save/load behavior.
- [x] Pass focused/AppTest coverage, the 397-test full suite, Ruff, compile,
  Streamlit startup and diff checks.

## Audit finding 13 - Loader decomposition - 2026-07-22

- [x] Inventory the loader phases, callers, sample shapes, fallbacks,
  exceptions, warnings, and inactive `is_alta` compatibility argument.
- [x] Characterize Standard/Split outputs, delimiters, decimals, encodings,
  malformed inputs, dates/times, read failures, and `is_alta` equivalence.
- [x] Extract only tolerant raw text-line reading into `_read_text_lines` while
  preserving its original position and public error behavior.
- [x] Pass the 16-test characterization group, 82-test loader/parser matrix,
  423-test full suite, scoped Ruff, compile, sample imports, startup, and diff
  checks.
- [x] Inventory all Split coastdown/meteo samples and keep fixture paths
  repository-relative without copying or rewriting sample data.
- [x] Extract only fixed row-15 header construction and the unchanged
  comma-only CSV read into `_read_coastdown_table`.
- [x] Cover every Split coastdown sample plus the meteo owner's record count,
  keys, timestamps, numeric values, raw ordering break, and duplicates.
- [x] Pass the same 29 pre/post checks, 16 focused, 62 coastdown, 33 meteo,
  13 sample-data, 423 full-suite, scoped Ruff, compile, startup, and diff checks.
- [x] Inventory both real Standard header families and the Split low, high, and
  combined layouts, including exact normalization and required-column errors.
- [x] Extract only post-Pandas alias mapping and required-column validation into
  `_validate_coastdown_columns`, preserving normalization order and diagnostics.
- [x] Cover BOM, whitespace, capitalization, duplicate, empty, unexpected, and
  missing columns without adding aliases or duplicating Split integration tests.
- [x] Pass 19 public pre/post checks, 5 focused, 20 loader, 66 coastdown,
  13 sample-data, 427 full-suite, scoped Ruff, compile, startup, and diff checks.
- [x] Map coastdown metadata and run times through parsing, committed state,
  automatic weather synchronization, correction, comparison, Results, and export.
- [x] Add characterization only for real millisecond timestamps, concrete meteo
  matches, nearest/tie/duplicate/order behavior, the 300-second boundary,
  time-only fallback, midnight, malformed inputs, and retained traceability.
- [x] Record without fixing the current `HH:MM`/`MM:SS` precedence and
  cross-date time-only fallback behavior.
- [x] Pass 9 focused temporal checks, the 85-test integration/AppTest matrix,
  436-test full suite, Ruff, compile, startup, and diff checks.
- [x] Extract only per-run coastdown start-time parsing into one private helper,
  leaving file-date discovery before Pandas and all synchronization untouched.
- [x] Pin helper return types, exact debug messages, milliseconds, missing and
  malformed values, elapsed forms, legacy fallbacks, and `HH:MM` ambiguity.
- [x] Pass the focused helper, 10 temporal, 86 integration/AppTest, and
  437 full-suite tests plus scoped Ruff, compile, startup, and diff checks.
- [x] Reassess the remaining loader after four extractions: complexity was still
  52 with 61 branches and 233 statements, so finding 13 remained In Progress at
  that checkpoint.
- [x] Pass the 70-test focused loader matrix, 437-test full suite, and diff check.
- [x] Extract only line-1/line-3 test-date discovery into a private header helper;
  preserve the caller's missing-date debug write and exception point.
- [x] Cover current date formats, delimiter choice, both-pass ordering,
  malformed metadata, diagnostics, and isolated unexpected failures.
- [x] Pass the 76-test focused loader suite, 443-test full suite, scoped Ruff,
  compile, Streamlit startup, and diff checks.
- [x] Reassess finding 13 after the header extraction: the remaining interval
  pipeline and Standard/Split representation branch are cohesive, so further
  extraction would move coupled state without improving ownership. Completed.

## Audit finding 14 - Stale Split session state - 2026-07-22

- [x] Inventory all nine candidate keys across active and legacy readers,
  writers, persistence, callbacks, dynamic lookups, tests, and documentation.
- [x] Remove new writes and persistence for the conclusive first-batch keys
  `mass_input_mode` and `split_source_files`.
- [x] Preserve old snapshot dictionaries while preventing obsolete flat-state
  values from leaking across test switches.
- [x] Keep canonical mass state and `split_input_sources` behavior unchanged.
- [x] Pass focused/AppTest coverage, the 400-test full suite, scoped Ruff,
  compile validation, Streamlit startup, and diff checks.
- [x] Remove active `data_info` writes and persistence while preserving the
  field in old snapshot dictionaries.
- [x] Retain `split_processed_at` as observable parser-processing metadata and
  verify its explicit-write and save/load behavior remains unchanged.
- [x] Pass second-batch focused/AppTest coverage, the 400-test full suite,
  scoped Ruff, compile validation, Streamlit startup, and diff checks.
- [x] Retain `weather_data_split` for legacy weather reads and `excel_buffer`
  for the legacy visible download and its stale-export invalidation paths.
- [x] Retain `split_ambient_version` and `split_processed_at` because signatures
  and counters do not replace their observable version and timestamp metadata.
- [x] Recover a malformed legacy ambient version only when a real ambient
  mutation records version 1; preserve valid version increments.
- [x] Pass retention-batch focused/AppTest coverage, the 402-test full suite,
  scoped Ruff, compile validation, Streamlit startup, and diff checks.
- [x] Remove `using_split_method` and `test_method` from active initialization,
  persistence, new-test creation, and routing dependencies.
- [x] Preserve valid old snapshot fields through a page-private resolver for
  direct legacy pages without restoring them into active flat state.
- [x] Cover single-key, dual-key, malformed, switching, round-trip,
  canonical-routing, direct-page, and idempotent-load behavior.
- [x] Pass final-batch focused/AppTest coverage, the 407-test full suite,
  scoped Ruff, compile validation, Streamlit startup, and diff checks.

## Audit finding 15 - Documentation ownership and workflow - 2026-07-21

- [x] Inventory current guidance, trackers, the automatic-selection plan, and
  directly referenced documentation against active navigation and imports.
- [x] Correct active page names and parser, weather, results, and exporter ownership.
- [x] Mark superseded milestones and round-local design limitations as historical.
- [x] Separate implemented automatic-selection behavior from deferred work.
- [x] Preserve the coefficient sign ambiguity during finding 15; resolve it
  separately in finding 19 without changing calculation behavior.
- [x] Verify paths, ownership statements, Markdown links, non-document scope, and diff hygiene.

## Audit finding 16 - Streamlit orchestration coverage - 2026-07-20

- [x] Cover new Split test creation with canonical fixed-condition keys.
- [x] Cover legacy reopening and canonical-key precedence through the active
  app load path.
- [x] Cover save/switch isolation and rename-only editing.
- [x] Run an incomplete active snapshot through `AppTest` and Results routing.
- [x] Pass focused/full tests, Ruff, compile, and diff checks.

## Audit finding 17 - Behavioral test conversion - 2026-07-21

- [x] Inventory and classify all 18 source-inspection tests and duplicated validator cases.
- [x] Replace three low-risk diagnostic source checks with rendered-output tests.
- [x] Pass focused/full tests, Ruff, compile validation, and diff checks.
- [x] Consolidate five pure-module source checks into one runtime import-boundary test.
- [x] Pass second-batch focused/full tests, Ruff, compile validation, and diff checks.
- [ ] Optional follow-up: consolidate duplicate coefficient-CV and time-group behavioral validator cases.
- [x] Replace the five remaining page source checks with practical interaction coverage.
- [x] Add the five remaining architecture modules to the runtime boundary test.
- [x] Confirm zero `inspect.getsource` tests remain.
- [x] Confirm the behavioral missing-coefficient guarantee and mark finding 17 complete.
- [x] Re-run final-batch focused/full tests, Ruff, compile validation, and diff checks.

## Audit finding 19 - Split coefficient sign guidance - 2026-07-23

- [x] Treat the existing Split calculation and positive road-load outputs as canonical.
- [x] Reproduce `F0 = 139.4112` and `F2 = 0.646178` from the Eliezer samples.
- [x] Confirm positive values through correction, comparison, Results, and export.
- [x] Correct only conflicting guidance; preserve formulas, outputs, and UI behavior.
- [x] Pass 62 focused tests, 13 sample-data tests, the 435-test full suite,
  compile of 74 Python files, scoped Ruff, and diff checks.
- [x] Mark finding 19 Completed.

## Audit finding 2 - Fixed-condition state compatibility - 2026-07-20

- [x] Trace fixed temperature and pressure through new-test creation, saved test snapshots, editing, loading and Split coefficient calculation.
- [x] Store new fixed-condition inputs in the canonical `split_fixed_temperature` and `split_fixed_pressure` keys while retaining legacy keys.
- [x] Migrate legacy-only saved tests at load time without overriding canonical Split values.
- [x] Add focused regression coverage for creation, legacy loading, canonical loading and canonical precedence.
- [ ] Optional follow-up: manually create and reopen one fixed-condition test in
  the running Streamlit app; automated coverage closes finding 2.

## Results page visual fixes - 2026-06-24
- [x] Replace the `st.columns`/`st.metric` consolidated summary in `pages/page_split_results.py` with a single HTML card (`split-summary-card`), matching the requested 3-row layout: pairs + conformity, F0/F2/energy grid, CV F0/F2 diagnostic row.
- [x] Drive the card's conformity icon (✅/❌/⚠️) from `analysis["time_summary"]["passed"]` (the real Split normative time validation), not from `core/split_results.py`'s CV-F0/F2-based `conformity_status`.
- [x] Reword `split_results_status_conforming`/`split_results_status_nonconforming` in `translations.py` to drop the Standard-style "(CV F0/F2 <= 10%)" parenthetical; add `split_results_status_inconclusive` for the new card and time-check rows.
- [x] Add `is_meteo_sync_warning()` classifier and `_split_warnings_by_audience()` in `pages/page_split_results.py`; route critical pair warnings through `st.warning` and meteo-sync warnings into a closed `st.expander` with a counted title.
- [x] Rewrite `_render_deviation_summary()` to show the six real Split normative metrics (CV Delta t high+/high-/low+/low- <= 2.5%, opposite-direction mean diff high/low <= 10%) via `format_split_time_group_label()`/`format_split_opposite_time_label()`, with CV F0/F2 shown separately and explicitly labeled diagnostic/non-normative.
- [x] Add all new PT/EN strings to `translations.py` (card labels, diagnostic label, meteo-sync expander title, deviation-table column headers/section titles).
- [x] Add/update regression tests in `tests/test_split_results_formatting.py` for the conformity mapping, card HTML (status/color/escaping), warning classifier/splitter, expander grouping and the six-metric deviation table.
- [x] Merge the validation and deviation UI into one `Validação dos resultados`
  section while retaining the coefficient and normative-time tables.
- [x] Remove the duplicate conformity banners, weather status card and weather
  warning rendering from the main page without changing warning payloads,
  traceability or Excel export.
- [x] Pass compile checks and all 17 focused Results-page tests.
- [x] Run the 450-test full suite after showing the diff: 449 passed and the
  unrelated auto-selection page test below errored identically in isolation.
- [x] Repair
  `test_render_submits_default_constraints_and_advanced_search_settings`,
  using one options/index-aware radio mock for direct and column-container calls.
- [ ] Reconcile the Streamlit lower-bound contract: `requirements.txt`
  declares 1.60.0 while `test_streamlit_dependency.py` still requires 1.55.0.
- [ ] Manually validate the consolidated card, merged validation section and
  absence of duplicate/weather alerts in the running Streamlit app with a real
  selected-pair set.

## Sidebar application version footer - 2026-07-28

- [x] Set the canonical `APP_VERSION` to `1.0.1`.
- [x] Reuse `APP_VERSION` in the existing page title and the shared sidebar footer.
- [x] Run targeted compile and diff checks.

## UI modernization

Approved plan: [docs/ui_modernization_plan.md](../docs/ui_modernization_plan.md)

- [x] Phase 1 - Theme and application shell
- [x] Phase 2 - Vehicle and interval workflow
- [ ] Phase 3 - Pair analysis and automatic selection
- [ ] Phase 4 - Comparison, results and charts
- [ ] Phase 5 - Responsive and accessibility validation
