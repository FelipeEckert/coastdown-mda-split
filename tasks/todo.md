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
- [x] Main Split navigation now has Vehicle Data, Interval Selection, Coefficient Calculation and Split Results.
- [x] Coefficient Calculation tab manually selects high+, low+, high- and low- before calculating.
- [x] Coefficient Calculation tab calculates direction +, direction - and arithmetic pair average.
- [x] Coefficient Calculation supports fixed or synchronized ambient conditions.
- [x] Coefficient Calculation stores corrected direction +, direction - and pair-average F0/F2.
- [x] `split_results` and `split_comparison_pairs` share canonical `f0_prime_*`, `f2_prime_*`, `F0_*` and `F2_*` keys.
- [x] Calculation summary, comparison table/cards and Split Results read the same canonical coefficient keys with legacy fallback.
- [x] Keep the latest calculated coefficient summary visible after Streamlit reruns.
- [x] Ambient mode, fixed temperature or fixed pressure changes invalidate calculated results and comparison cards.
- [x] Coefficient Calculation tab can add complete ida/volta pairs to `split_comparison_pairs`.
- [x] Comparison table includes four runs, raw/corrected means, directional ambient conditions, energy status and warnings.
- [x] Comparison cards show directional meteo sync data and identify the conditions used by climatic correction.
- [x] Split Results page has final summary selection and basic Excel download.
- [ ] Run manual regression in the app before first commit: create test, replace high, replace low, remove low, replace meteo, remove meteo.
- [ ] Run manual regression with one high-only CSV and confirm calculation remains blocked with friendly warning.
- [ ] Run manual regression with one low-only CSV and confirm calculation remains blocked with friendly warning.
- [ ] Run manual regression with high+low CSVs and confirm final f'0/f'2 match expected values.
- [ ] Run manual regression with four selected runs and confirm ida, volta and pair-average f'0/f'2.
- [ ] Run manual regression with explicit combined mode and confirm high-only/low-only combined files block calculation.

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
- [x] Energy is calculated from corrected `F0_mean/F2_mean` and shown in Split results, comparison table and cards.
- [x] `core/split_energy.py` delegates explicitly to `core.calculations.calcular_energia(F0_mean, F2_mean)`.
- [x] Save the inherited formula origin as `standard_formula_calcular_energia` with unit `MJ/km`.
- [x] Save `energy=None` only when corrected F0/F2 are unavailable.
- [x] Save calculated `energy`, `energy_unit`, `energy_profile`, `energy_origin` and `energy_status` in results and comparison pairs.
- [x] Add tests for corrected-coefficient use, unavailable correction, comparison propagation and explicit units.
- [ ] Validate the provenance and normative applicability of the inherited city/highway constants and 55/45 weighting.

## Excel export status
- [x] Basic Split Excel export exists.
- [x] Export includes summary, selected results, four ida/volta components, Delta t and subinterval traceability.
- [ ] Add the four component-level ambient records and weather sync audit to Excel.
- [ ] Review final workbook layout, labels and units before release.

## Known gaps and next steps
- [ ] Parser needs more real combined/full coastdown examples to validate heuristics beyond synthetic full-coastdown tests.
- [ ] Split workflow/results still contain English literal labels; convert important user-facing strings to `translations.py`.
- [ ] Review whether interval changes after upload should automatically reparse or show a stronger "reparse required" cue.
- [ ] Review date/timezone policy for files with ambiguous dates or missing timezone metadata.
- [ ] Add meteo synchronization details to Split Excel export without applying climatic correction implicitly.
- [ ] Continue visual polish after functional validation; keep technical meteo warnings collapsed by default.
- [ ] Keep `sample_data/Split/` and `sample_data/Standard/` separated as validation datasets for each method.
