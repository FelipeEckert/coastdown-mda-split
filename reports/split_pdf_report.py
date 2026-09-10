"""Split PDF export contract; rendering is intentionally not implemented.

See docs/split_pdf_report_plan.md for canonical sources and future page layout.
This module must not import calculation, selection, parser or UI modules.
"""

from datetime import datetime


def export_split_final_results_to_pdf(
    *,
    final_results: dict,
    vehicle_data: dict,
    deviation_analysis: dict,
    graph_series: list[dict],
    test_name: str,
    generated_at: datetime,
    test_metadata: dict | None = None,
    language: str = "pt",
) -> bytes:
    """Reserve PDF export from a consistent, caller-prepared canonical snapshot.

    final_results contains the consolidated values and sole selected_pairs list.
    vehicle_data contains vehicle identification and already normalized masses.
    deviation_analysis supplies normative time checks, diagnostic coefficient
    statistics, weather checks, limits and warnings. graph_series supplies
    prepared times_s/speeds_kmh points, record identity and data_mode.

    Optional test_metadata holds test_date, responsible_engineer, operator,
    driver, location, service_identifier, report_identifier, start_time,
    end_time, method, configuration and equipment when available. These fields
    belong to the test, not vehicle_data; missing values must not be invented.
    generated_at is the report timestamp, not a fallback test date.
    language selects PT/EN presentation (default: pt).

    Future rendering must preserve inputs, signs, units, selection order and
    supplied statuses. It must never recalculate F0/F2, energy, CV, weather
    corrections or normative validation, nor normalize masses or parse runs.
    Missing optional data stays unavailable; no numerical fallback is allowed.

    Raises:
        NotImplementedError: Always, until PDF rendering is implemented.
    """
    raise NotImplementedError("Split PDF rendering is not implemented yet.")
