# Coastdown MDA Split UI modernization plan

Status: Phase 1 completed on 2026-07-28; phases 2–5 pending.

## Objective and scope

Modernize the Coastdown MDA Split interface as a dark navy technical
dashboard with electric-blue accents while keeping Python and Streamlit.
Improve hierarchy, spacing, typography, sidebar test cards, controls, alerts,
metrics, tables, charts, and responsive behavior without changing the Split
method or application behavior.

The implementation must prefer native Streamlit theming, layout, and
components. Reusable Python helpers and scoped CSS are allowed only when a
native feature cannot express an approved requirement safely.

This plan does not authorize a migration to React, Tailwind, another frontend
framework, a custom JavaScript navigation layer, or new UI dependencies.

## Visual reference

Primary visual reference:
[Coastdown UI concept](ui-reference/coastdown-ui-concept.png).

The reference establishes visual direction rather than a pixel-perfect
contract. Its approved characteristics are:

- dark navy application and sidebar surfaces;
- restrained electric-blue emphasis for selection, focus, and primary actions;
- compact technical-dashboard density;
- clearly separated cards and sections;
- consistent outline-style icons;
- strong hierarchy between page title, section title, labels, values, and
  metadata;
- visible status, warning, and active-test states.

## Current UI strengths

- The app already uses a dark theme and `layout="wide"`.
- The sidebar correctly owns global settings, test management, and test status.
- Main and nested navigation use `st.tabs` with `on_change="rerun"` and
  `.open` checks, so only the selected page or sub-tab renders.
- Test cards already use keyed native bordered containers.
- Dialogs, native alerts, metrics, dataframes, and stable widget keys are
  established.
- Multiple tests, active-test switching, persisted state, translations, and
  compatibility migrations are already centralized in the application shell.
- Plotly presentation has a shared Split-specific theme helper.
- Results and comparison views already preserve Split-specific traceability and
  validation semantics.

## Current visual problems

- The current charcoal palette does not create the layered navy depth of the
  reference.
- Global CSS overrides primary buttons to green, conflicting with the approved
  electric-blue interaction language.
- Styling is fragmented between global CSS and page-specific HTML/CSS.
- Broad selectors target Streamlit and BaseWeb internals, increasing upgrade
  risk.
- A global dataframe selector hides the first column even though Streamlit
  provides `hide_index=True`.
- Structural emoji icons are inconsistent across platforms and do not match the
  reference's technical icon system.
- Some sidebar action targets are smaller than the approved interaction size.
- Frequent dividers and repeated subheaders weaken section hierarchy.
- Five- and six-column metric grids become cramped on narrower viewports.
- Native dataframes, HTML tables, Pandas styling, and page-local colors do not
  yet share one visual language.
- Deprecated `use_container_width=True` remains in active UI code.
- Custom tables and fixed-width column layouts can force horizontal scrolling
  outside the cases where wide technical data genuinely requires it.

## Approved design tokens

### Core and semantic colors

| Token | Value | Purpose |
|---|---:|---|
| App background | `#07111F` | Main application canvas |
| Sidebar background | `#081522` | Global controls and test management |
| Primary surface | `#0D1B2B` | Inputs, cards, and secondary regions |
| Raised surface | `#112438` | Emphasized cards and nested sections |
| Border | `#2A4058` | Default card and widget separation |
| Primary action | `#1264C8` | Primary buttons and committed actions |
| Electric-blue accent | `#3A9CFF` | Focus, active state, links, and selection |
| Primary text | `#F4F8FC` | Headings and body text |
| Secondary text | `#A9B6C7` | Captions, metadata, and helper text |
| Success | `#2DD36F` | Confirmed and conforming states |
| Warning | `#F5B82E` | Caution and pending validation |
| Error | `#FF6B6B` | Blocking and nonconforming states |

White text against the primary-action color has approximately 5.7:1 contrast.
Primary and secondary text, the electric-blue accent, and the semantic
foreground colors meet or exceed the approved dark-background contrast targets.
Contrast must be rechecked in the rendered Streamlit application because
component states and derived background colors can alter the effective result.

Global theme values belong in `.streamlit/config.toml`. Existing custom HTML
islands should consume Streamlit theme variables or shared semantic variables
instead of repeating raw hexadecimal values.

### Typography

- Keep the built-in sans-serif stack initially; do not add a font package or
  remote-font dependency.
- Preserve the existing small, medium, and large user-selectable font modes.
- Use 16px as the medium body baseline and do not reduce normal body text below
  14px in the small mode.
- Use a body line height near 1.5.
- Use a descending heading scale with no skipped semantic heading levels.
- Use sentence casing for page titles, section titles, buttons, and labels.
- Keep numeric precision and units defined by the Split presentation contract;
  typography changes must not reformat calculation values.

### Spacing and radius

- Use a 4/8px rhythm: `4`, `8`, `12`, `16`, `24`, and `32`.
- Use small gaps inside compact control groups, 16px section padding, and
  24–32px separation between major page sections.
- Prefer Streamlit container `gap` and `st.space()` over decorative dividers.
- Use an 8px button radius and a 10–12px card radius.
- Prefer borders and surface contrast over glow and heavy shadows.
- Avoid fixed widths for normal content; reserve them for bounded technical
  visualizations that have an explicit overflow strategy.

### Interaction and accessibility

- Prefer Material Symbols over emoji for navigation, actions, status, and data
  icons.
- Keep icon family, fill style, and sizing consistent within each hierarchy.
- Give interactive controls a target of at least 44×44px where Streamlit and
  the surrounding layout allow it.
- Keep visible keyboard focus indicators.
- Do not rely on hover or color alone to communicate state.
- Pair semantic color with text, icon, badge, or native alert type.
- Use native disabled behavior and ensure disabled controls remain visibly
  distinct.
- Keep optional transitions between 150 and 300ms, avoid layout-shifting
  animation, and respect reduced-motion preferences.
- Preserve visible or programmatically meaningful labels; do not introduce
  empty widget labels.
- Keep errors close to the affected control or section.

## Native Streamlit features to prefer

- `.streamlit/config.toml` for global colors, fonts, radii, borders, sidebar,
  dataframe, and chart palette.
- `st.logo()` or existing native image rendering for approved brand assets.
- `st.container(border=True, key=...)` for cards and grouped sections.
- `st.container(horizontal=True)` for action and metric rows that should wrap.
- `st.columns()` only for stable form pairs, comparison grids, or deliberate
  width ratios; avoid more than four columns when possible.
- `st.metric(..., border=True)` for compact result and status summaries.
- Material Symbols through supported `icon=` parameters and Streamlit Markdown.
- `st.badge()` for active, synchronized, pending, and validation states.
- `st.space()` and container gaps instead of repeated horizontal rules.
- Native `st.info`, `st.warning`, `st.error`, and `st.success` with semantic
  icons.
- `st.dataframe` with `column_config`, `hide_index=True`, and native formatting.
- Default stretch behavior or `width="stretch"`/`width="content"` instead of
  deprecated `use_container_width`.
- Existing `st.dialog` flows for focused create, edit, delete, and confirmation
  actions.
- Existing lazy `st.tabs(..., on_change="rerun")` plus `.open` checks.
- `st.expander` for advanced settings and optional diagnostics.
- `st.segmented_control` only where a small mode choice benefits from it and
  widget-state compatibility has been characterized first.
- `st.form` only where batching inputs improves rerun behavior without changing
  the current save or invalidation contract.

## Cases where custom CSS is justified

Custom CSS is justified only for:

- the per-session font-size preference, which cannot be represented by static
  theme configuration;
- keyed active and inactive sidebar test-card treatment;
- minimum interaction sizing or alignment that Streamlit cannot express through
  native layout parameters;
- responsive behavior for existing custom result and comparison tables;
- semantic row spans, cell highlights, and comparison states that native
  dataframes cannot reproduce;
- a restrained active-card accent edge if native borders do not provide enough
  hierarchy.

Custom CSS is not justified for global button, input, alert, tab, metric, or
dataframe theming when `.streamlit/config.toml` or native parameters cover the
requirement. New CSS must:

- be scoped through stable keyed containers or owned class names;
- avoid broad BaseWeb, generated-class, or global HTML-table selectors;
- use semantic variables instead of page-local color literals;
- preserve visible focus and native disabled states;
- include a narrow-screen rule when the styled structure can overflow;
- avoid JavaScript and custom components unless a future requirement cannot be
  met with native Streamlit.

## Reusable component opportunities

- Keep `render_test_card()` as the single test-card renderer.
- Extend the existing global font-size/style entry point instead of adding a
  styling framework.
- Keep the existing Split Plotly theme helper as the owner of Plotly colors,
  surfaces, axes, legend, and hover styling.
- Add a small metric-row helper only after the same native horizontal pattern is
  repeated across multiple pages.
- Keep table formatting local when the coefficient, comparison, and final-result
  schemas have different semantics.
- Reuse shared semantic tokens across existing custom HTML islands, but do not
  force unrelated cards into one speculative abstraction.
- Keep Material icon names close to their owning UI unless repetition proves a
  shared mapping is useful.

## Streamlit limitations relative to the reference

- Streamlit cannot reproduce the reference navigation rail, tab geometry, icon
  discs, and card interactions pixel-for-pixel without brittle DOM styling.
- Native tabs may scroll on narrow screens instead of becoming a custom step
  navigator.
- Whole-card click handling is not native; explicit test and action controls
  should remain.
- Native date and number inputs retain Streamlit and browser behavior rather
  than custom inline steppers.
- Wide technical tables may still require horizontal scrolling on small screens.
- Hosted Deploy and menu chrome are not fully controlled by application code.
- A perfectly fixed sidebar footer may require CSS and can overlap content;
  normal native placement is safer.
- Streamlit remains desktop-dashboard-first. Responsive work should prioritize
  readable stacking and safe overflow rather than attempting to recreate a
  mobile-native interface.

## Invariants that must not change

The modernization is presentation work only. Every implementation phase must
preserve:

- all Split calculations, equations, signs, units, precision, and validation
  thresholds;
- `Delta V = abs(V_initial - V_final)`;
- parser behavior, supported input structures, configurable intervals, warnings,
  and traceability;
- separation between Standard and Split logic;
- all session-state keys, test snapshots, migrations, and compatibility aliases;
- creation, editing, deletion, activation, switching, and persistence of tests;
- active navigation IDs, tab labels, widget keys, and `current_page` behavior
  unless a separately characterized migration is approved;
- lazy main-tab, pair-analysis-tab, and parser-review-tab rendering;
- translations and Portuguese/English behavior;
- weather loading, date mismatch warnings, fixed conditions, time-only
  synchronization, and weather correction;
- automatic-selection algorithms, constraints, budgets, progress, replacement,
  fallback, and merge behavior;
- comparison selection, final-result availability, deviation analysis, and
  compatibility repair;
- Excel generation, export content, signatures, caches, filenames, and download
  behavior;
- existing assets and brand proportions;
- the supported Streamlit dependency range;
- performance characteristics, especially avoiding hidden-tab execution or
  additional expensive reruns.

## Implementation phases

### Phase 1 — Theme and application shell

Status: Completed on 2026-07-28.

Scope:

- establish the approved native dark navy theme;
- remove the conflicting green primary-button override;
- narrow global CSS and remove unsafe global dataframe/table rules;
- modernize the sidebar, test-card hierarchy, status presentation, and
  structural icons;
- preserve all test-management and navigation behavior.

Expected files:

- `.streamlit/config.toml`;
- `app.py`;
- `docs/ui_modernization_plan.md`;
- `tasks/todo.md`;
- `tasks/lessons.md`.

No page, calculation, parser, translation, export, or workflow file is expected
in this phase. Existing orchestration and lazy-tab tests should run unchanged;
tests should be edited only if a real presentation contract requires new
behavioral coverage.

Implementation result:

- the native Streamlit theme now owns the layered dark-navy palette, electric
  blue primary state, semantic colors, borders, radii, and dataframe surfaces;
- the shell and the existing `render_test_card()` renderer use native badges,
  Material icons, horizontal containers, and stretch-width controls where
  practical;
- remaining CSS is scoped to runtime font-size support, shell spacing,
  sidebar test-card geometry, 44px card actions, and the existing pair-energy
  presentation;
- the conflicting green primary-button override, global table-header override,
  global dataframe first-column hiding, custom status HTML, and fixed sidebar
  footer were removed;
- all 20 active `st.dataframe` calls were verified to set `hide_index=True`
  before the global index CSS was removed.

### Phase 2 — Vehicle and interval workflow

Status: Pending.

Scope:

- modernize vehicle information and Split mass sections;
- use bordered native cards and responsive metric rows;
- improve interval configuration hierarchy and parser-review presentation;
- replace deprecated width parameters in the touched pages;
- preserve all input keys, mass invalidation, parsing, draft/processed state,
  and lazy parser-review tabs.

Expected files:

- `pages/page_2_dados_veiculo.py`;
- `pages/page_split_workflow.py`;
- `tasks/todo.md`;
- `tasks/lessons.md`.

Relevant existing tests may be updated only when necessary to characterize
rendered behavior; calculation and parser modules are not expected to change.

### Phase 3 — Pair analysis and automatic selection

Status: Pending.

Scope:

- normalize dense controls, summaries, alerts, progress, and advanced settings;
- improve manual pair selection and saved-pair card hierarchy;
- modernize automatic-selection settings and diagnostics;
- preserve nested lazy tabs, candidate generation, constraints, search budgets,
  replacement dialogs, fallback confirmation, and state keys.

Expected files:

- `pages/page_split_coefficient_calculation.py`;
- `pages/page_split_auto_selection.py`;
- `tasks/todo.md`;
- `tasks/lessons.md`.

Focused page and automatic-selection tests may change only to cover deliberate UI
behavior. Core selection, calculation, correction, and validation modules are
not expected to change.

### Phase 4 — Comparison, results and charts

Status: Pending.

Scope:

- align final comparison and results cards, tables, metrics, and alerts with the
  shared design tokens;
- preserve semantic comparison origins, selection, conformity, diagnostics, and
  traceability;
- update the existing Split Plotly theme;
- use native dataframe formatting where it preserves the required structure;
- retain custom HTML only for row spans or visual states native dataframes cannot
  represent;
- replace deprecated width parameters in the touched pages.

Expected files:

- `pages/page_split_final_comparison.py`;
- `pages/page_split_results.py`;
- `pages/page_split_coefficient_calculation.py` only for chart rendering calls
  still owned there;
- `utils/split_graphs.py`;
- `tasks/todo.md`;
- `tasks/lessons.md`.

Results, comparison, graph, and export tests may be updated only for presentation
contracts. Calculation, consolidation, deviation, and export payload logic must
remain unchanged.

### Phase 5 — Responsive and accessibility validation

Status: Pending.

Scope:

- validate the complete application at approved viewport widths;
- verify keyboard focus, labels, contrast, target sizes, disabled states, table
  overflow, reduced motion, and long translated labels;
- verify all font-size modes and both languages;
- correct only issues found during validation;
- complete final regression, visual, and documentation checks.

Expected files:

- no application file is planned in advance;
- only files with verified responsive or accessibility defects should change;
- `tasks/todo.md`;
- `tasks/lessons.md`.

Any application change discovered here must remain presentation-only and receive
focused validation for its owning page.

## Validation requirements

Each implementation phase must:

- inspect the current diff and preserve unrelated user changes;
- run `python -m py_compile` for every changed Python file;
- run focused tests for each touched page or shell behavior;
- run `tests/test_app_orchestration.py` and `tests/test_split_tab_routing.py`
  whenever shell, navigation, tabs, or shared state presentation changes;
- verify hidden tabs do not execute;
- run the full test suite at the end of each completed phase or before merging
  multiple phases;
- run `git diff --check`;
- stage files individually;
- update `tasks/todo.md` and record durable decisions in `tasks/lessons.md`;
- avoid adding dependencies unless separately approved.

Manual Streamlit validation must cover:

- widths near 375px, 768px, 1024px, and 1440px;
- Portuguese and English;
- small, medium, and large font modes;
- empty state, one test, multiple tests, active/inactive tests, and long test
  names;
- combined and separate Split input modes;
- missing, valid, mismatched-date, and time-only weather states;
- unprocessed, stale, invalid, and valid interval configurations;
- manual pair analysis, graph analysis, and automatic selection;
- empty and populated comparison/results states;
- Excel generation and download availability;
- keyboard traversal, visible focus, native disabled behavior, and control
  labels;
- primary text contrast of at least 4.5:1 and secondary text contrast of at
  least 3:1 on dark surfaces;
- interaction targets near 44×44px where practical;
- no unintended horizontal page scrolling; explicit table scrolling is allowed
  when necessary;
- no content hidden by the sidebar footer, dialogs, tabs, or hosted chrome;
- no layout-shifting decorative animation and acceptable reduced-motion
  behavior.

## Progress checklist

- [x] Phase 1 — Theme and application shell (completed 2026-07-28)
- [ ] Phase 2 — Vehicle and interval workflow (pending)
- [ ] Phase 3 — Pair analysis and automatic selection (pending)
- [ ] Phase 4 — Comparison, results and charts (pending)
- [ ] Phase 5 — Responsive and accessibility validation (pending)
