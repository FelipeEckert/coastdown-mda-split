# Coastdown MDA Split

Streamlit application for coastdown analysis using the Split method.

This repository was created from the Coastdown MDA Standard codebase, but the
visible workflow is now quarantined for Split migration. Standard pages and
calculations remain in the repository as inherited legacy code until each piece
is either removed or explicitly reused as neutral infrastructure.

## Current Split Workflow

1. Create a test with a full/combined CSV or separate high/low CSV files.
2. Confirm vehicle data and effective mass.
3. Configure high and low Split intervals.
4. Review extracted interval traceability.
5. Calculate and save Split results.
6. Aggregate selected results and export an Excel report.

Norm defaults are high `90-70 km/h` with reference `80 km/h`, and low
`45-35 km/h` with reference `40 km/h`. They are defaults only, not hardcoded
rules.
