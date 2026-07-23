# AGENTS.md — Coastdown MDA Split

## Project Overview

This repository is the **Coastdown MDA Split** project.

It was created from the existing `cd-streamlit` / Coastdown MDA Standard codebase and now has a separate active application workflow dedicated to the **Split method** for coastdown analysis according to ABNT NBR 10312.

The Standard and Split methods must remain separated. This project may reuse neutral infrastructure from the Standard application, but the Split parser, workflow, calculations, validation rules and reports must be reviewed and implemented specifically for the Split method.

---

## Core Principle

Do **not** blindly reuse Standard-method logic.

Only reuse UI/infrastructure. All Split logic must be **reviewed, rethought, and explicitly validated**.

Reusable areas may include:

- Streamlit layout;
- sidebar and multi-test management;
- session state structure;
- assets/logos;
- translations;
- meteorological loading/synchronization;
- Excel export infrastructure;
- general utility functions.

Split-specific areas must remain owned and validated by Split modules:

- parser;
- data model;
- workflow/pages;
- coefficient calculations;
- validation rules;
- final report content.

---

## Current Ownership

- Active navigation: `page_2_dados_veiculo.py`, `page_split_workflow.py`,
  `page_split_coefficient_calculation.py`, `page_split_final_comparison.py`, and
  `page_split_results.py`.
- Automatic Selection is a sub-tab rendered by `page_split_auto_selection.py`.
- `data/split_parser.py` owns Split parsing; `data/split_exporters.py` owns the
  Split workbook; `data/weather_loader.py` owns weather-file loading.
- `core/split_*.py` modules own Split calculations, correction, validation,
  automatic selection, state, comparison, and results.
- Finding 18 removed all inherited Standard pages and their closed dependency
  island. `core/calculations.py` retains only the neutral energy kernel used by
  Split, while `data/loaders.py` retains the shared active coastdown loader.

---

## Development Rules

Before any non-trivial change:

1. Read this `AGENTS.md`
2. Inspect the current code
3. Make a short implementation plan
4. Keep changes minimal
5. Avoid unrelated refactors

Always:

- run: `python -m py_compile <file>`
- stage files individually
- explain every change
- document important decisions in `tasks/lessons.md`.

Never:

- use `git add .`
- mix Standard and Split logic
- change formulas silently
- delete inherited Standard files/pages without first explaining why;

---

## Tracking discipline

This project uses `tasks/todo.md` and `tasks/lessons.md` as active project memory.

- Every functional change must review and update `tasks/todo.md` with current tasks, completed items, open bugs, pending validations and next steps.
- Every technical decision, important bug or durable implementation lesson must review and update `tasks/lessons.md`.
- Do not finish a task without checking both files.
- Use `todo.md` for operational status: pending, in progress, done, discovered during development.
- Use `lessons.md` for durable knowledge that should guide future changes.
- Do not rewrite these files entirely unless explicitly requested. Prefer targeted edits to relevant sections.

---

## Split Parser Requirements

The Split parser is expected to differ from the Standard parser and must be flexible regarding input file organization.

### Supported input structures

The parser must support multiple real-world formats:

1. **Separate files**
   - one file for high-speed interval
   - one file for low-speed interval

2. **Single combined file**
   - both intervals in one dataset

3. **Full coastdown file**
   - one continuous run
   - intervals must be extracted dynamically

⚠️ The parser **must NOT assume** that high/low intervals come as separate files.

---

### Functional requirements

The parser must:

1. load high-speed and low-speed data from either separate or combined files;
2. identify time columns corresponding to configured speed subintervals;
3. extract and sum subinterval times to compute `Delta t1` and `Delta t2`;
4. preserve run/pass direction when available;
5. support user-defined intervals (no hardcoding);
6. use norm values only as defaults;
7. record full traceability:
   - file used
   - run used
   - columns used
   - intervals used
8. warn clearly if required intervals are not found.

---

### Default extraction example

```text
High interval 90–70 km/h:
  Delta t2 = t(90–85) + t(85–80) + t(80–75) + t(75–70)

Low interval 45–35 km/h:
  Delta t1 = t(45–40) + t(40–35)
```

---

## Delta V Convention

```text
Delta V = abs(V_initial - V_final)
```

❌ Do NOT use:

```text
Delta V = V_final - V_initial
```

---

## Split Coefficient Equations

```text
f'0,n =
Me / (V2² - V1²)
×
[
  (Delta V2 / Delta t2) × V1²
  -
  (Delta V1 / Delta t1) × V2²
]

f'2,n =
Me / (V2² - V1²)
×
[
  (Delta V1 / Delta t1)
  -
  (Delta V2 / Delta t2)
]
```

---

## Validation Rules

```text
Me > 0
Delta t1 > 0
Delta t2 > 0
V2 > V1
Delta V1 > 0
Delta V2 > 0
```

Also:

```text
high_start > high_reference > high_end
low_start > low_reference > low_end
```

---

## Current Project Structure

```text
coastdown-mda-split/
├── app.py
├── AGENTS.md
├── translations.py
├── requirements.txt
├── pages/
├── core/
├── data/
├── docs/
├── tests/
├── utils/
└── tasks/
```

---

## Coding Style

- snake_case
- small pure functions
- explicit validation
- readable errors

---

## Documentation

Track everything in:

- tasks/todo.md
- tasks/lessons.md

---

## Initial Development Phase (Completed)

The app identity, active Split navigation, Split parser base, Split modules, and
coefficient function are implemented. Current pending work belongs in
`tasks/todo.md`; detailed implementation history belongs in `tasks/lessons.md`.

---

## What Not To Do

Do not:

- mix Standard and Split workflows
- hardcode intervals
- assume file format
- silently change formulas

---

## Response Expectations

Always report:

- files changed
- changes made
- validations run
- assumptions
- next steps
