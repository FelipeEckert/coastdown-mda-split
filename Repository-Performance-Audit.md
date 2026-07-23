# Repository Performance Audit

Date: 2026-07-23

## Outcome

Three material bottlenecks were confirmed:

1. weather-file normalization parses timestamps row by row;
2. automatic selection materializes the full four-group Cartesian product, and Target ranking deep-copies every candidate;
3. synchronized weather matching rebuilds and sorts the same weather records once per run and is repeated on Streamlit reruns while that mode is open.

Coastdown parsing, ordinary warm reruns, Plotly rendering, deviation-cache hits, and on-demand Excel export were measured and are not current bottlenecks.

## Measurement basis

- Windows, Python 3.12.10, Pandas 3.0.0, Streamlit 1.57.0, Plotly 6.7.0, openpyxl 3.1.5.
- Repository samples: the separate Eliezer Split files and `AGRICULTR_SPLIT.csv` (902,063 bytes; 9,476 valid weather records).
- Timings are wall-clock medians unless identified as `cProfile` or `tracemalloc` measurements.
- Streamlit reruns were measured with `streamlit.testing.v1.AppTest`; these are server-side timings, not browser paint or network timings.

## Confirmed bottlenecks and priority

| Priority | Bottleneck | Affected files/functions | Evidence | Recommended low-risk fix |
|---|---|---|---|---|
| P0 | Row-by-row weather datetime parsing | `data/weather_loader.py`: `_normalize_weather_frame()`, `_parse_datetime()`, `read_weather_file()` | Loading 9,476 rows: **10.46 s** median over five measured reloads. `cProfile`: 10.37 s of 15.47 s in `_parse_datetime()`/per-row `pd.to_datetime()`, plus 2.74 s in `DataFrame.iterrows()`. One vectorized `pd.to_datetime()` call took **16–18 ms** and produced zero timestamp differences on all 9,476 sample rows. | Parse each datetime column as a Pandas Series once, preserving the current ISO/day-first rules and per-row ambiguity warnings. Then replace `iterrows()` with a lighter row traversal or vectorized numeric columns. Prove record-for-record equality on current weather fixtures before adopting it. |
| P0 | Target ranking deep-copies every generated candidate | `core/split_selection_algorithms.py`: `rank_candidates_by_target()` | For 10,000 real-shaped candidates, Energy ranking took **0.106 s**; Target ranking took **4.975 s**. `tracemalloc` attributed **128.0 MiB** of additional peak allocations to Target ranking versus 17.1 MiB for Energy ranking. The cause is one `deepcopy(candidate)` per candidate before adding three scalar score fields. | Use a top-level copy for score fields, or keep scores in lightweight ranking records and materialize only retained candidates. Nested candidate data is read-only in this function; retain an immutability regression test. |
| P1 | Exact automatic selection materializes an `n⁴` candidate set and emits one progress update per candidate | `core/split_candidate_generation.py`: `generate_full_split_candidates_exact()`; `core/split_pair_candidate.py`: `build_algorithm_split_pair_candidate()`; `pages/page_split_auto_selection.py`: `progress_callback()` | The sample has 10 runs in each high+/low+/high-/low- group: **10,000** combinations before MAD and 8,100 after the page-equivalent filter. Unfiltered generation took **2.289 s**; `tracemalloc` measured **99.6 MiB** peak candidate allocations. Page-equivalent Energy selection with default constraints took **2.564 s**, including 1.237 s for 3,000 constrained-set evaluations. Generation calls the Streamlit progress callback **once per attempted candidate**—8,100 UI updates for this sample. | First throttle progress to integer-percent changes (at most 101 updates). Then precompute invariant per-direction high/low calculations and reuse them across opposite-direction combinations while keeping final candidate order and values identical. Do not change formulas, MAD, search limits, or selection rules. Removing the `n⁴` contract itself is not a low-risk change. |
| P1 | Weather synchronization repeats normalization and sorting for every run, then repeats the whole batch on unrelated reruns | `core/weather_sync.py`: `_weather_records()`, `_closest()`, `sync_weather_to_run()`; `core/split_weather_context.py`: `synchronize_weather_for_split_runs()`; `pages/page_split_auto_selection.py`: `render()` | Synchronizing 40 parsed runs against 9,476 records took **410 ms** median. Under `cProfile`, `_weather_records()` consumed 1.154 s (52.5% of the profiled 2.197 s) and `_closest()` 0.287 s (13.1%). `_weather_records()` is called once per run, and `_closest()` sorts all candidates. In weather mode the page invokes the batch synchronization on every Streamlit rerun. | Normalize valid weather records once at the start of `synchronize_weather_for_split_runs()` and reuse them for all runs. Replace full sorting with a single-pass minimum plus explicit tie detection. Re-measure; only then add a small session cache keyed by Split input version, weather content/version, sync limit, and weather limits if rerun cost remains material. |
| P2 | Multi-test persistence deep-copies large state values key by key | `app.py`: `save_active_test_state()`, `load_test_state()`, `TEST_STATE_KEYS` | With the 9,476 weather records plus real parsed/source data, save and load each took about **142 ms** and **140 ms**. The same logical run structures are present under several state keys and are traversed separately. This occurs on test activation/editing, not every ordinary rerun. | Defer unless test switching is visibly slow. If addressed, copy one payload dictionary per save/load so `deepcopy()` can preserve shared references and traverse repeated objects once; verify test isolation and legacy snapshot behavior. |

## Measured non-bottlenecks

| Area | Evidence | Conclusion |
|---|---|---|
| Streamlit reruns | Warm `AppTest` medians with real parsed data: Vehicle 90 ms, Workflow 102 ms, Pair Calculation 139 ms, Final Comparison 125 ms, Graphs 144 ms, idle Automatic Selection 148 ms, Results 225 ms. Main pages and nested analysis tabs render only the active section. | Keep the current lazy routing. Do not add fragments or broad rerun suppression without real-browser evidence. |
| Coastdown file parsing | Separate high file: 13.7 ms; separate low file: 21.2 ms; combined file: 18.2 ms. `parse_split_sources()` over 40 runs: 0.62 ms. | No parser optimization is justified. |
| Plotly | Four default graphs, including server-side figure construction and JSON serialization: about 52 ms and 20 KB total. | No Plotly cache is justified. Browser validation remains useful, especially with unusually many selected runs. |
| Repeated final calculations | Deviation analysis cache hit: 0.15 ms for five pairs and 2.8 ms for 100 pairs. Final consolidation and display work remained inside the warm rerun timings above. | Existing signature cache is effective. |
| Excel export | Five pairs: signature 0.78 ms, workbook 27 ms. Stress case at 100 pairs: signature 18.3 ms, workbook 126 ms. Export runs only after the explicit button and reuses bytes by signature. | Keep the existing on-demand cache. Moving export into another cache layer would add complexity without useful gain. |

## Recommended order

1. Vectorize weather timestamp parsing and verify output equality.
2. Remove full deep copies from Target ranking.
3. Normalize weather records once per synchronization batch and avoid sorting for nearest-match lookup.
4. Throttle automatic-selection progress updates; then reuse invariant directional calculations if timing remains unacceptable.
5. Re-run the same benchmark set and complete the already-pending real-browser timing check.
6. Leave state-copy, Plotly, coastdown parser, deviation cache, and Excel paths unchanged unless later measurements regress.

## Constraints preserved

This audit made no production-code changes. The recommendations do not change Split formulas, validation rules, interval conventions, selection constraints, report contents, or application behavior. Any implementation should be guarded by record-for-record or candidate-for-candidate regression tests before performance is compared again.
