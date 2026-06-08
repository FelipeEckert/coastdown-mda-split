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
- [ ] Confirm final unit wording and normative notation for report/export

## Phase 4 - UI workflow
- [x] Adapt vehicle data page
- [x] Create Split file loading/parser review page
- [x] Create Split analysis/calculation page
- [x] Create Split validation behavior for incomplete high/low inputs
- [x] Create Split results page
- [x] Add separate input slots for high-speed, low-speed and meteo files
- [x] Allow replacing/removing high, low and meteo inputs separately
- [x] Invalidate Split-derived state when files change
- [x] Invalidate Split-derived state when input mode changes
- [x] Show Split input mode message based on parsed high/low records
- [x] Show upload slots from explicit mode: separate high/low or single combined
- [ ] Manual UX test for replacing only high, only low and only meteo in an existing test
- [ ] Manual UX test for switching input mode in an existing test
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

## Current operational tracker - 2026-06-08
- [x] Split file input roles implemented: high-speed, low-speed and meteo have distinct slots.
- [x] Edit/replace/remove flow implemented for high, low and meteo files.
- [x] CSV replacement clears `split_parsed_runs`, `split_results`, `split_final_results`, `excel_buffer` and increments `split_input_version`.
- [x] Meteo replacement/removal clears derived final/export state and resets time-only sync.
- [x] Parser blocks incomplete high/low combinations instead of generating partial or position-based intervals.
- [x] Input mode is explicit in the UI and saved as `split_input_mode`.
- [x] Split Results page has final summary selection and basic Excel download.
- [ ] Run manual regression in the app before first commit: create test, replace high, replace low, remove low, replace meteo, remove meteo.
- [ ] Run manual regression with one high-only CSV and confirm calculation remains blocked with friendly warning.
- [ ] Run manual regression with one low-only CSV and confirm calculation remains blocked with friendly warning.
- [ ] Run manual regression with high+low CSVs and confirm final f'0/f'2 match expected values.
- [ ] Run manual regression with explicit combined mode and confirm high-only/low-only combined files block calculation.

## Meteo status
- [x] Weather CSV loader remains neutral infrastructure reused by Split.
- [x] Weather file can be added, replaced and removed from the Split test editor.
- [x] Meteo replacement/removal invalidates stale final/export state.
- [ ] Apply meteorological correction/sync to the Split coefficient calculation workflow.
- [ ] Add Split-specific meteo audit details to results/export.

## Excel export status
- [x] Basic Split Excel export exists.
- [x] Export includes summary, selected results, high/low files, runs, Delta t and subinterval traceability.
- [ ] Add meteo inputs and weather sync audit when Split meteo integration is complete.
- [ ] Review final workbook layout, labels and units before release.

## Known gaps and next steps
- [ ] Parser needs more real combined/full coastdown examples to validate heuristics beyond synthetic full-coastdown tests.
- [ ] Split workflow/results still contain English literal labels; convert important user-facing strings to `translations.py`.
- [ ] Review whether interval changes after upload should automatically reparse or show a stronger "reparse required" cue.
- [ ] Keep `sample_data/Split/` and `sample_data/Standard/` separated as validation datasets for each method.
