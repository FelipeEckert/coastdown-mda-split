# Split Automatic Pair Selection - Technical Audit

Date: 2026-06-19

This document maps the current Split manual calculation contract before adding
automatic pair-selection algorithms. No algorithm, UI flow, or calculation
behavior was changed in this audit.

## 1. Files Inspected

- `app.py`
- `pages/page_split_workflow.py`
- `pages/page_split_coefficient_calculation.py`
- `pages/page_split_final_comparison.py`
- `pages/page_split_results.py`
- `pages/page_4_selecao_algoritmo.py`
- `core/split_calculations.py`
- `core/split_corrections.py`
- `core/split_energy.py`
- `core/split_comparison.py`
- `core/split_results.py`
- `core/split_display.py`
- `core/split_state.py`
- `core/weather_sync.py`
- `data/split_parser.py`
- `data/weather_loader.py`
- `translations.py`
- `tests/test_split_calculations.py`
- `tests/test_split_comparison.py`
- `tests/test_split_corrections.py`
- `tests/test_split_display.py`
- `tests/test_split_energy.py`
- `tests/test_split_graphs.py`
- `tests/test_split_interval_step.py`
- `tests/test_split_results.py`
- `tests/test_split_sample_data_import.py`
- `tests/test_weather_sync.py`

The requested `utils/weather_sync.py` and `utils/weather_loader.py` do not exist
in this repository. The active equivalents are `core/weather_sync.py` and
`data/weather_loader.py`.

## 2. Parsed Split Run Contract

Parsed runs are stored in:

```python
st.session_state["split_parsed_runs"]
```

The committed parser snapshot is produced by:

```python
data.split_parser.parse_split_sources(...)
core.split_state.store_processed_split_intervals(...)
```

The structure is:

```python
{
    "high": [record, ...],
    "low": [record, ...],
    "warnings": [message, ...],
}
```

Each high/low record currently contains these relevant fields:

- `interval_name`: `high` or `low`
- `run_id`: source run identifier
- `heading`: expected to be `+` or `-` for complete manual calculation
- `filename`: source file name
- `source_role`: high, low, combined/full role declared by the loader/UI
- `start_kmh`, `end_kmh`, `reference_kmh`
- `step_kmh`
- `delta_v_kmh`
- `delta_t_s`
- `subintervals`: matched speed-bin labels
- `source_columns`: source columns used to build `delta_t_s`
- `start_timestamp`
- `start_time_str`
- `warnings`

Input sources are stored separately in:

```python
st.session_state["split_input_sources"]
```

The parser preserves source metadata there, including file role and content hash
when available. Candidate identity should not rely on `run_id` alone because run
numbers may repeat across files. A robust identity for automatic candidates should
include at least:

```python
(interval_name, heading, filename, source_role, run_id)
```

If available, include source hash from `split_input_sources` for stronger
deduplication:

```python
(interval_name, heading, filename, content_sha256, run_id)
```

This supports the conceptual identities:

```python
("high", "+", run_id)
("low", "+", run_id)
("high", "-", run_id)
("low", "-", run_id)
```

while avoiding collisions between separate files or repeated run labels.

## 3. Manual Split Pair Calculation Flow

The active Split navigation imports `page_split_coefficient_calculation`,
`page_split_final_comparison`, and `page_split_results`. The inherited
`pages/page_4_selecao_algoritmo.py` is not in the active Split navigation and
still writes to legacy Standard-style state such as `calculated_pairs` and
`pares_finais_selecionados`; it must not be reused as the Split algorithm
implementation.

The manual calculation flow is:

1. `pages/page_split_coefficient_calculation.py` reads
   `split_parsed_runs["high"]` and `split_parsed_runs["low"]`.
2. `core.split_comparison.group_split_records_by_direction()` groups records into:
   - `high_plus`
   - `low_plus`
   - `high_minus`
   - `low_minus`
   - `invalid`
3. The UI requires one record for each of the four components.
4. `_effective_mass()` reads `vehicle_info["effective_mass"]` or `total_mass`.
5. `calculate_complete_split_pair()` calculates:
   - direction `+`: high+ with low+
   - direction `-`: high- with low-
   - arithmetic pair mean of f'0/f'2
6. Ambient conditions are built by either:
   - `fixed_ambient_conditions(temperature, pressure)`
   - `weather_sync_ambient_conditions(weather_sync)`
7. `apply_split_pair_correction()` applies climatic correction, stores corrected
   F0/F2, and calculates energy when both directions are corrected.
8. The result is appended to `st.session_state["split_results"]` and assigned to
   `st.session_state["split_last_calculated_result"]`.
9. The user explicitly adds the latest result to the final comparison.
10. `build_split_comparison_pair(..., selection_source="manual")` builds the saved
    comparison item.
11. `add_split_comparison_pair()` appends it to:

```python
st.session_state["split_comparison_pairs"]
```

Current manual pairs enter the comparison with `selected=True`.

## 4. Calculation Functions To Reuse

The current reusable calculation chain is:

```python
calculate_complete_split_pair(
    high_plus,
    low_plus,
    high_minus,
    low_minus,
    effective_mass,
    config,
)
apply_split_pair_correction(result, ambient_conditions)
build_split_comparison_pair(result, selection_source=...)
```

The lower-level coefficient function is:

```python
core.split_calculations.calculate_split_coefficients(...)
```

It validates:

- `Me > 0`
- `Delta t1 > 0`
- `Delta t2 > 0`
- `V2 > V1`
- `Delta V1 > 0`
- `Delta V2 > 0`
- `high_start > high_reference > high_end`
- `low_start > low_reference > low_end`

`calculate_complete_split_pair()` is the correct Split pair engine for automatic
candidate generation because it already enforces the complete four-component
contract and uses the same formulas as manual calculation.

## 5. Climatic Correction Contract

Fixed ambient mode:

```python
fixed_ambient_conditions(temperature_c, pressure_kpa)
```

This creates four component records with `sync_method="fixed"` and applies the
same temperature and pressure to both directions.

Weather sync mode:

```python
sync_weather_to_run(record, weather_data, max_time_delta_seconds=300, ...)
weather_sync_ambient_conditions(weather_sync)
```

The UI syncs all four components independently:

- `high_plus`
- `low_plus`
- `high_minus`
- `low_minus`

`weather_sync_ambient_conditions()` then averages conditions by direction:

- `temp_plus_used` and `press_plus_used` from high+ and low+
- `temp_minus_used` and `press_minus_used` from high- and low-

The correction is direction-specific:

- f'0/f'2 for direction `+` are corrected with plus ambient averages.
- f'0/f'2 for direction `-` are corrected with minus ambient averages.
- final corrected `F0_mean` and `F2_mean` are arithmetic means of corrected plus
  and minus results.

If either direction lacks complete ambient values, partial corrected direction
values may exist, but `correction_available=False`, `F0_mean=None`,
`F2_mean=None`, and `energy=None`.

Weather records loaded by `data.weather_loader.read_weather_file()` provide:

- `timestamp`
- `temp_c`
- `baro_kpa`
- `wind_ms`
- `wind_direction`
- `wind_unit`
- `timezone`
- `warnings`
- `source_file`

Weather sync records preserve:

- `matched`
- `sync_method`
- `run_datetime`
- `weather_datetime`
- `time_delta_seconds`
- `temperature`
- `pressure`
- `wind_speed`
- `wind_direction`
- `warnings`
- `weather_record`
- `source_file` added by the UI wrapper

Important warning sources include missing run timestamps, no weather records,
records outside the time limit, time-only fallback, ambiguous dates, missing
timezone, equally close records, missing wind, invalid wind, and unknown wind
units.

## 6. Energy Contract

Split energy is calculated by:

```python
core.split_energy.calculate_split_energy(F0_mean, F2_mean)
```

This delegates to:

```python
core.calculations.calcular_energia(F0_mean, F2_mean)
```

Expected inputs:

- `F0_mean`: corrected F0 in N
- `F2_mean`: corrected F2 in `N/(km/h)^2`

Return fields:

- `energy`
- `energy_unit`: `MJ/km`
- `energy_status`: `calculated`
- `energy_profile`: `standard_formula_calcular_energia`
- `energy_origin`: `core.calculations.calcular_energia`
- `F0_used`
- `F2_used`

The current project already documents that the inherited energy constants and
profile still need normative provenance review.

## 7. `split_comparison_pairs` Contract

The active final comparison source is:

```python
st.session_state["split_comparison_pairs"]
```

Items are list entries, not a dict keyed by pair id. `normalize_split_comparison_pairs()`
can tolerate older dict-shaped data and adds fallback technical ids.

Current complete-pair fields include:

- `id`
- `selection_source`: `manual`, `algorithm`, or `unknown`
- `selected`
- `high_plus`, `low_plus`, `high_minus`, `low_minus`
- `result_plus`, `result_minus`, `result_pair_mean`
- `corrected_result_plus`, `corrected_result_minus`, `corrected_pair_mean`
- `high_plus_file`, `high_plus_run`, `high_plus_direction`,
  `high_plus_delta_t_s`, `high_plus_timestamp`
- `low_plus_file`, `low_plus_run`, `low_plus_direction`, `low_plus_delta_t_s`,
  `low_plus_timestamp`
- `high_minus_file`, `high_minus_run`, `high_minus_direction`,
  `high_minus_delta_t_s`, `high_minus_timestamp`
- `low_minus_file`, `low_minus_run`, `low_minus_direction`,
  `low_minus_delta_t_s`, `low_minus_timestamp`
- `effective_mass`
- `v1_reference_kmh`, `v2_reference_kmh`
- `delta_v1_kmh`, `delta_v2_kmh`
- `f0_prime_plus`, `f2_prime_plus`
- `f0_prime_minus`, `f2_prime_minus`
- `f0_prime_mean`, `f2_prime_mean`
- compatibility aliases: `f0_plus`, `f2_plus`, `f0_minus`, `f2_minus`,
  `f0_prime`, `f2_prime`
- `correction_available`
- `F0_plus`, `F2_plus`, `F0_minus`, `F2_minus`
- `F0_mean`, `F2_mean`
- compatibility aliases: `F0`, `F2`
- `F0_unit`, `F2_unit`
- `cv_F0_percent`, `cv_F2_percent`
- `ambient_mode`, `ambient_source`
- `ambient_by_component`
- `temp_plus_used`, `press_plus_used`
- `temp_minus_used`, `press_minus_used`
- `wind_plus_ms`, `wind_minus_ms`
- component aliases: `temp_high_plus`, `press_high_plus`, `wind_high_plus`,
  `temp_low_plus`, `press_low_plus`, `wind_low_plus`, `temp_high_minus`,
  `press_high_minus`, `wind_high_minus`, `temp_low_minus`, `press_low_minus`,
  `wind_low_minus`
- weather summary: `weather_high`, `weather_low`, `weather_records`,
  `weather_sync`, `weather_match_count`, `temp_c`, `baro_kpa`, `wind_ms`
- `energy`, `energy_unit`, `energy_profile`, `energy_origin`,
  `energy_details`, `energy_status`
- `warnings`
- older compatibility fields: `high_file`, `high_run`, `high_direction`,
  `high_delta_t_s`, `high_timestamp`, `low_file`, `low_run`,
  `low_direction`, `low_delta_t_s`, `low_timestamp`

There is no active Split support for `selected_by_energy_algo` or
`selected_by_target_algo` in `split_comparison_pairs`. The active visual contract
currently supports `selection_source="algorithm"` as a generic algorithm origin,
plus selected-row, uncorrected-reference, and high-CV styling.

## 8. Final Comparison And Results Consumption

`pages/page_split_final_comparison.py` reads `split_comparison_pairs`.

Important behaviors:

- uncorrected pairs are forced to `selected=False`
- only corrected pairs have a checkbox
- selected corrected pairs are returned by
  `selected_corrected_split_comparison_pairs()`
- selected-pair statistics use `consolidate_split_final_results()`
- the final action stores `split_final_results` and sets
  `navigate_to_results=True`

`pages/page_split_results.py` also reads `split_comparison_pairs` directly and
calls:

```python
consolidate_split_final_results(comparison_pairs)
```

The final result includes only pairs with `selected=True` according to
`core.split_results.selected_split_final_pairs()`.

## 9. Required Fields For Automatic Candidates

Automatic candidates should build the same comparison-pair contract and enter the
table with:

```python
selection_source = "algorithm"
selected = False
```

Candidate generation needs:

- four parsed records: `high_plus`, `low_plus`, `high_minus`, `low_minus`
- stable component identity including role, direction, run id, and source
- `effective_mass`
- committed `split_interval_config`
- ambient mode and either fixed conditions or weather sync inputs
- `weather_data` and meteo source file when sync mode is used
- target F0/F2 only for target-ranking mode
- ranking metadata if desired, stored without changing final selection semantics

If visual distinction between energy and target algorithms is required, add
Split-specific fields deliberately, for example:

```python
selected_by_energy_algo = True
selected_by_target_algo = False
algorithm_rank = 1
algorithm_score = ...
```

The current table does not consume those fields, so that should be a separate,
explicit UI update.

## 10. Extractable Pure Engine

The next implementation step should extract a pure helper, likely in
`core/split_comparison.py` or a new `core/split_auto_selection.py`, that receives
records and ambient inputs and returns a comparison-pair-shaped candidate:

```python
build_split_candidate_pair(
    high_plus,
    low_plus,
    high_minus,
    low_minus,
    effective_mass,
    config,
    ambient_conditions,
    selection_source="algorithm",
    selected=False,
)
```

Internally it should call the existing manual engine:

```python
calculate_complete_split_pair(...)
apply_split_pair_correction(...)
build_split_comparison_pair(...)
```

This avoids duplicated formulas and keeps manual and automatic candidates on the
same calculation path.

## 11. Risks

- The inherited `page_4_selecao_algoritmo.py` already contains algorithm code, but
  it writes to Standard-style state and sets `selected=True`; reusing it directly
  would violate the Split contract.
- `selection_source="algorithm"` exists, but energy-vs-target visual flags do not
  exist in active Split comparison rendering.
- Current manual comparison insertion defaults to `selected=True`; automatic
  insertion must override this to `selected=False`.
- Run identity by numeric `run_id` alone is not robust across separate files or
  repeated exports.
- Weather sync is currently partly UI-wrapped because `_sync_weather()` adds
  `source_file` from session state; automatic generation should move that wrapper
  into a reusable helper.
- Generating all four-component combinations can grow quickly. Ranking logic
  should stream or prune only after the candidate calculation contract is proven.
- Energy uses corrected means and an inherited Standard formula whose constants
  still need normative provenance review.
- Final Results currently accepts selected pairs even if missing corrected F0/F2,
  but Final Comparison prevents uncorrected selection. Automatic insertion should
  still avoid marking uncorrected candidates selected.

## 12. Proposed Next Step

1. Add focused pure tests for a candidate-builder helper that proves automatic
   candidates match manual calculation output for the same four records and
   ambient conditions.
2. Implement the candidate-builder helper with `selected=False` and
   `selection_source="algorithm"`.
3. Add a pure candidate enumeration helper that groups parsed runs by component and
   yields complete candidate identities without duplicates.
4. Add ranking helpers for lowest energy and target proximity using only the
   candidate contract.
5. Only after the pure layer is covered, connect a small Split UI action that adds
   candidates to `split_comparison_pairs` without selecting them for final results.

## Round 2 - Automatic Candidate Helper

Implemented pure module:

```python
core.split_pair_candidate
```

Main function:

```python
build_algorithm_split_pair_candidate(
    *,
    high_plus_run,
    low_plus_run,
    high_minus_run,
    low_minus_run,
    vehicle_data,
    correction_context=None,
)
```

It does not import Streamlit and does not access `st.session_state`. It receives
all required data by parameter and reuses the same calculation path as the manual
flow:

```python
calculate_complete_split_pair(...)
apply_split_pair_correction(...)
build_split_comparison_pair(...)
```

The returned dict is compatible with `split_comparison_pairs` and is forced to:

```python
candidate["selection_source"] = "algorithm"
candidate["selected"] = False
```

### Run Usage

The helper `build_split_run_usage(...)` returns a tuple with one entry per required
component, always in this order:

```python
(
    ("high", "+", run_id, filename, source_role, source_hash),
    ("low", "+", run_id, filename, source_role, source_hash),
    ("high", "-", run_id, filename, source_role, source_hash),
    ("low", "-", run_id, filename, source_role, source_hash),
)
```

Missing values are represented by `"<missing>"`, so incomplete traceability does
not break identity construction. The hash field uses the first available value
from `content_sha256`, `source_content_sha256`, `source_sha256`, or `file_sha256`.

### Stable Signature

The helper `split_candidate_signature(candidate)` returns `candidate["run_usage"]`
when present, normalized as a tuple of tuples. If a candidate does not yet have
`run_usage`, the signature is rebuilt from its `high_plus`, `low_plus`,
`high_minus`, and `low_minus` component records.

This signature changes when any one of the four component runs changes and does
not depend on the generated pair id.

### Correction Context

`correction_context` intentionally remains small in this round. It can provide:

- `ambient_conditions`: already-resolved conditions, passed directly to
  `apply_split_pair_correction`
- `weather_sync`: four-component sync dict, converted by
  `weather_sync_ambient_conditions`
- fixed values such as `temperature_c`/`pressure_kpa`, converted by
  `fixed_ambient_conditions`
- optional config under `config`, `split_interval_config`, or `interval_config`
- optional `pair_id`

This round does not move the UI weather wrapper or implement bulk weather
synchronization for generated candidates.

## Round 3 - Ranking And Top-k Selection

Implemented pure module:

```python
core.split_selection_algorithms
```

Public functions:

```python
rank_candidates_by_energy(candidates)
rank_candidates_by_target(candidates, target_f0, target_f2)
select_top_k_candidates(ranked_candidates, k, avoid_repeated_runs=True)
mark_algorithm_source(candidates, algorithm)
```

The module does not import Streamlit and does not access `st.session_state`.

### Energy Ranking

`rank_candidates_by_energy()` reads candidate energy from the canonical
`energy` field. It also accepts `mean_energy` and `mean_energy_corrected` as
legacy fallbacks. Candidates without finite numeric energy are ignored.

Valid candidates are sorted by:

```python
(energy, split_candidate_signature(candidate))
```

The signature is converted to a comparable key for deterministic tie-breaking.
No ranking score is added because `energy` is already the score.

### Target Ranking

`rank_candidates_by_target()` reads corrected coefficients from canonical
`F0_mean` and `F2_mean`, with known aliases `F0`, `F2`, `mean_f0`,
`mean_f2`, `mean_f0_corrected`, and `mean_f2_corrected`.

`target_f0` and `target_f2` must be finite and non-zero. Candidates without
finite corrected F0/F2 are ignored. Score is:

```python
error_f0 = abs(f0 - target_f0) / abs(target_f0)
error_f2 = abs(f2 - target_f2) / abs(target_f2)
target_score = math.hypot(error_f0, error_f2)
```

Returned candidates are copies with:

```python
target_score
target_error_f0_pct
target_error_f2_pct
```

### Top-k Selection

`select_top_k_candidates()` receives already-ranked candidates and returns:

```python
selected_candidates, metadata
```

Metadata contains:

```python
{
    "requested_k": k,
    "selected_count": ...,
    "avoid_repeated_runs": ...,
    "skipped_repeated_count": ...,
    "skipped_invalid_usage_count": ...,
    "warnings": [...],
}
```

When `avoid_repeated_runs=True`, repetition is checked by exact items inside
`candidate["run_usage"]`. Same numeric `run_id` does not conflict if the usage
item differs by interval type, direction, file, role, or hash. If a candidate has
missing or invalid `run_usage`, it is skipped and counted in metadata.

The function does not backfill with repeated candidates when fewer than `k`
non-repeating candidates are available; it returns fewer candidates and records a
warning.

### Algorithm Origin

`mark_algorithm_source()` returns copies with:

```python
selected = False
selection_source = "algorithm"
algorithm_source = "energy"  # or "target"
```

It also fills `selected_by_energy_algo` and `selected_by_target_algo` as
compatibility hints, but those flags are not the source of truth.

## Round 4 - Normative Time Validation

Implemented pure module:

```python
core.split_time_validation
```

Public functions:

```python
coefficient_of_variation_percent(values)
opposite_mean_difference_percent(mean_a, mean_b)
extract_split_candidate_times(candidates)
validate_split_selected_times(candidates, cv_limit_pct=2.5, opposite_mean_limit_pct=10.0)
```

The module does not import Streamlit and does not access `st.session_state`.

### Norm Interpretation

For a selected set of complete Split candidates, the diagnostic builds four time
lists:

```python
high_plus
high_minus
low_plus
low_minus
```

Each list represents measured Delta t values for one reference speed and one
direction. The diagnostic checks:

- `CV(high_plus) <= 2.5%`
- `CV(high_minus) <= 2.5%`
- `CV(low_plus) <= 2.5%`
- `CV(low_minus) <= 2.5%`

It also checks the opposite-direction mean differences:

- high: `abs(mean(high+) - mean(high-)) / average(mean(high+), mean(high-)) <= 10%`
- low: `abs(mean(low+) - mean(low-)) / average(mean(low+), mean(low-)) <= 10%`

### Time Extraction

`extract_split_candidate_times()` reads component times from the comparison-pair
contract. It first checks optional `time_components[component]["delta_t_s"]`,
then canonical fields such as `high_plus_delta_t_s`, and finally falls back to
embedded component records such as `candidate["high_plus"]["delta_t_s"]`.

This means no additional candidate fields were required in round 4.

### Pass Status

`validate_split_selected_times()` returns detailed `groups`, `opposite_direction`
and `warnings`.

Overall `passed` follows this rule:

- `False` if any evaluable check fails
- `True` if every CV and opposite-direction check is evaluable and passes
- `None` if at least one check is not evaluable, but no evaluable check failed

With only one selected candidate, CV is not evaluable because each group has one
time. That produces `passed=None` and warnings instead of a failure.

This round is diagnostic only. It does not filter ranked candidates and does not
integrate with UI or Final Comparison.

## Round 5 - Exact Complete Candidate Generation

Implemented pure module:

```python
core.split_candidate_generation
```

Public functions:

```python
split_runs_by_role_and_heading(split_parsed_runs)
estimate_full_candidate_count(grouped_runs)
iter_full_candidate_run_groups(grouped_runs)
generate_full_split_candidates_exact(...)
```

The module does not import Streamlit and does not access `st.session_state`.

### Grouping

`split_runs_by_role_and_heading()` reads the current parsed-run contract:

```python
{
    "high": [...],
    "low": [...],
    "warnings": [...],
}
```

It groups records into:

```python
high_plus
low_plus
high_minus
low_minus
```

Records whose heading is not `+` or `-` are ignored and reported in warnings.
The grouped lists are sorted by source role, filename, run id, interval name and
Delta t for deterministic generation.

### Exact Count And Cartesian Product

The estimated exact candidate count is:

```python
len(high_plus) * len(low_plus) * len(high_minus) * len(low_minus)
```

`iter_full_candidate_run_groups()` yields complete run groups for the exact
cartesian product:

```python
high+ x low+ x high- x low-
```

Each yielded group is shaped for the round-2 candidate builder:

```python
{
    "high_plus_run": ...,
    "low_plus_run": ...,
    "high_minus_run": ...,
    "low_minus_run": ...,
}
```

### Candidate Building

`generate_full_split_candidates_exact()` uses
`build_algorithm_split_pair_candidate()` by default and accepts
`candidate_builder` injection for tests or future orchestration.

It returns:

```python
candidates, metadata
```

Metadata contains:

```python
{
    "mode": "exact",
    "estimated_total": ...,
    "attempted_count": ...,
    "generated_count": ...,
    "failed_count": ...,
    "skipped_count": ...,
    "group_counts": {
        "high_plus": ...,
        "low_plus": ...,
        "high_minus": ...,
        "low_minus": ...,
    },
    "warnings": [...],
}
```

Candidate-level exceptions are captured, counted and reported as warnings; one
bad combination does not abort the full generation.

### Safety Limit

`max_combinations` is an optional exact-mode guard. If the estimated total exceeds
the limit, generation is not attempted and metadata includes:

```text
Total estimated candidates exceeds max_combinations.
```

This prepares the later orchestration decision:

- small sets can use exact generation
- large sets can use a future optimized directional preselection path

This round does not implement preselection, ranking, top-k, UI, or Final
Comparison integration.

## Round 6 - Pure Exact Auto-selection Orchestrator

Implemented pure module:

```python
core.split_auto_selection
```

Main function:

```python
run_split_auto_selection_exact(
    split_parsed_runs,
    *,
    vehicle_data,
    correction_context=None,
    algorithm,
    k,
    target_f0=None,
    target_f2=None,
    avoid_repeated_runs=True,
    max_combinations=None,
    progress_callback=None,
    candidate_builder=None,
)
```

The module does not import Streamlit and does not access `st.session_state`.

### Flow

The orchestrator executes the exact-mode automatic selection pipeline:

```python
generate_full_split_candidates_exact(...)
rank_candidates_by_energy(...) or rank_candidates_by_target(...)
select_top_k_candidates(...)
mark_algorithm_source(...)
validate_split_selected_times(...)
```

It returns:

```python
selected_candidates, metadata
```

It does not add candidates to `split_comparison_pairs`.

### Algorithms

`algorithm="energy"` ranks generated candidates by corrected energy using
`rank_candidates_by_energy()`.

`algorithm="target"` requires `target_f0` and `target_f2`, then ranks by
normalized corrected F0/F2 distance using `rank_candidates_by_target()`.

Invalid algorithms and non-positive `k` raise `ValueError`.

### Selection And Origin

Top-k selection is delegated to `select_top_k_candidates()`, including optional
`avoid_repeated_runs` behavior based on `run_usage`.

Returned candidates are then passed through `mark_algorithm_source()`, preserving:

```python
selected = False
selection_source = "algorithm"
algorithm_source = "energy"  # or "target"
```

### Metadata

Final metadata has this shape:

```python
{
    "mode": "exact",
    "algorithm": "energy" | "target",
    "requested_k": k,
    "generated_count": ...,
    "ranked_count": ...,
    "selected_count": ...,
    "avoid_repeated_runs": ...,
    "generation": {...},
    "selection": {...},
    "time_validation": {...} | None,
    "warnings": [...],
}
```

`generation` is the exact-generation metadata, `selection` is the top-k metadata,
and `time_validation` is the normative time diagnostic for the suggested
candidates. Time validation is diagnostic only; it does not filter candidates in
this round.

If exact generation returns no candidates, the orchestrator returns an empty list,
preserves generation warnings, and does not attempt ranking.

This round still has no UI and no Final Comparison integration.

## Round 7 - Pure Merge With Final Comparison

Implemented pure module:

```python
core.split_comparison_merge
```

Public functions:

```python
comparison_pair_signature(pair)
merge_algorithm_candidates_into_comparison_pairs(
    existing_pairs,
    algorithm_candidates,
    *,
    algorithm_source,
)
```

The module does not import Streamlit and does not access `st.session_state`.
It receives the current comparison list and algorithm suggestions by parameter
and returns:

```python
updated_pairs, metadata
```

It does not write back to `split_comparison_pairs`; the future UI layer remains
responsible for assigning the returned list to session state.

### Duplicate Signature

`comparison_pair_signature()` prefers the automatic candidate identity:

```python
pair["run_usage"]
```

through `split_candidate_signature(pair)`. If `run_usage` is absent, it tries the
embedded complete-pair component records (`high_plus`, `low_plus`, `high_minus`,
`low_minus`). If those are also absent, it uses flattened comparison fields such
as `high_plus_run`, `high_plus_file`, `low_plus_run`, `low_plus_file` and their
minus-direction equivalents. Only when no component identity is available does
it fall back to `pair_id` or `id`.

This keeps duplicate detection tied to the four calculated Split passes instead
of the technical comparison id.

### Merge Behavior

New algorithm candidates are appended as copies with:

```python
selected = False
selection_source = "algorithm"
algorithm_source = "energy" | "target"
algorithm_sources = ["energy"]  # or ["target"]
selected_by_energy_algo = True/False
selected_by_target_algo = True/False
```

When a candidate has the same signature as an existing comparison pair, the
existing pair is not duplicated. Its main calculation fields, user label,
warnings, energy, F0/F2 values and `selected` state are preserved. The helper
only enriches algorithm-origin metadata.

Manual final selection always wins. If an existing duplicate was already marked:

```python
selected = True
```

that value remains true.

### Multiple Algorithm Origins

The helper stores accumulated algorithm origins in:

```python
algorithm_sources = ["energy", "target"]
```

and keeps the compatibility flags:

```python
selected_by_energy_algo
selected_by_target_algo
```

For duplicate pairs that originally entered manually, `selection_source` is left
unchanged so the original comparison provenance is not erased; algorithm
suggestions are traceable through `algorithm_sources` and the boolean flags.

### Metadata

The merge metadata has this shape:

```python
{
    "algorithm_source": "energy" | "target",
    "input_existing_count": ...,
    "input_candidate_count": ...,
    "output_count": ...,
    "added_count": ...,
    "duplicate_count": ...,
    "updated_existing_count": ...,
    "preserved_selected_count": ...,
    "warnings": [...],
}
```

This round still has no UI, no button, no automatic-selection sub-tab and no
write to `st.session_state`.
