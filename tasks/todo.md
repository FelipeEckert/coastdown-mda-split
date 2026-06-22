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
- [x] Adapt basic Excel export for Split
- [x] Include parser traceability
- [x] Include calculation inputs and outputs
- [x] Include validation warnings
- [ ] Add weather/meteo inputs and sync audit to Split Excel when calculation integration is finalized
- [ ] Decide final normative report layout and units wording

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
- [x] Manual pairs store `selection_source="manual"`; the table contract already supports future `selection_source="algorithm"`.
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
- [ ] Adapt the Split Excel exporter to the new selected-pair consolidation contract; the UI keeps export disabled until then.
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
- [ ] Add all four `ambient_by_component` records to Split results export/report.

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
- [ ] Review final workbook layout, labels and units before release.

## Round 11A - Split Results and final Excel report
- [x] Refactor Split Results as a read-only executive summary based on Final Comparison selections.
- [x] Reuse `consolidate_split_final_results()` and `analyze_split_selected_deviations()` without UI formula duplication.
- [x] Show vehicle data, final F0/F2, CVs, energy, validation, selected-pair table, weather and traceability.
- [x] Create pure `data/split_exporters.py` without Streamlit imports.
- [x] Export Resumo Final, Dados do Veículo, Pares Selecionados, Análise de Desvios, Tempos deltaT, Meteorologia and Rastreabilidade sheets.
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
- [ ] Add meteo synchronization details to Split Excel export without applying climatic correction implicitly.
- [ ] Continue visual polish after functional validation; keep technical meteo warnings collapsed by default.
- [ ] Validate the Final Comparison table manually with a larger number of pairs and narrow desktop widths.
- [ ] Manually recheck Final Comparison checkbox/batch/remove/results navigation with real browser state after the Streamlit session-state fix.
- [x] Add Split-specific Delta T conformity diagnostics for selected Final Comparison pairs by reusing `core/split_time_validation.py`.
- [ ] Connect future automatic Split selection to `selection_source="algorithm"` without importing the Standard algorithm workflow.
- [x] Audit the current manual Split pair calculation and comparison contracts before implementing automatic selection algorithms.
- [x] Extract a pure Split candidate-builder helper that reuses `calculate_complete_split_pair`, `apply_split_pair_correction` and `build_split_comparison_pair`.
- [x] Ensure future automatic Split candidates enter `split_comparison_pairs` with `selection_source="algorithm"` and `selected=False`.
- [x] Add pure ranking and top-k selection helpers for automatic Split candidates.
- [x] Add pure normative time diagnostics for selected automatic Split candidates.
- [x] Add pure automatic-candidate enumeration from grouped Split runs without UI state.
- [ ] Implement normative time/direction validation for generated automatic candidates before UI integration.
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
- [x] Confirm Split Excel is generated by `page_split_results.generate_split_excel`, not `data/exporters.py`.
- [ ] Stop eager Standard imports from `core/__init__.py` and `data/__init__.py` while preserving public compatibility where required.
- [ ] Split `data/loaders.py` into a neutral VBOX reader plus explicit Split and Standard adapters.
- [ ] Move `generate_split_excel` from the Streamlit page into a dedicated Split export module.
- [ ] Move the pure `calcular_energia(f0, f2)` kernel to a neutral module, keeping a compatibility wrapper in `core/calculations.py`.
- [ ] Mark old Split attempts in `core/calculations.py` as quarantined/deprecated and remove them only after confirming no external consumer imports them.
- [ ] Keep `core/corrections.py`, `data/exporters.py`, `utils/pair_time_analysis.py` and pages 3-6 isolated as Standard legacy.
- [ ] Review the inherited 3% rotational-inertia default in Vehicle Data against the final Split normative workflow.
- [ ] Update stale `app.py` comments that still describe pages 2-6 and inherited compatibility as the current architecture.

## Round 12A - Weather synchronization in Automatic Selection
- [x] Synchronize weather once per high/low run without mutating `split_parsed_runs`.
- [x] Validate wind above 3 m/s, temperature above 35 °C and missing required weather; keep pressure traceability-only.
- [x] Preserve four weather components, aggregate summary, correction context and warnings in candidates and comparison merge.
- [x] Rank by explicitly preferred corrected energy/F0/F2 fields while preserving fixed-mode fallbacks.
- [x] Add optional invalid-weather filtering, enabled by default in synchronized UI mode.
- [x] Show synchronization counters and compact candidate weather summaries/details.
- [x] Add pure-module, synchronization, validation, candidate, ranking, filtering and merge tests.
- [ ] Complete the required real-app manual validation with high/low/weather files, both filter states, merge, deviation analysis and Split Results.

## Round 10A - Final Comparison deviation analysis
- [x] Preserve the existing Final Comparison behavior in the `Tabela` sub-tab.
- [x] Analyze only pairs explicitly stored with `selected=True`.
- [x] Add pure F0/F2 sample CV, per-pair deviation and leave-one-out diagnostics.
- [x] Reuse Split time validation for the four deltaT groups and opposite-direction means.
- [x] Add configurable diagnostic alerts for wind above 3 m/s and temperature above 35 °C; pressure remains display-only.
- [x] Add PT/EN labels and unit coverage for the pure analysis module.
- [ ] Complete the required real-browser manual regression for both sub-tabs, selection persistence, weather alerts and Split Results navigation.
