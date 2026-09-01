# -*- coding: utf-8 -*-

"""
TEST GRAPH
==========

Aircraft Maintenance Intelligence Pipeline

Flow:

    Excel Data
         ↓
    Analytics
         ↓
    Detect Statistical Anomaly
         ↓
    ┌─────────────────────────────┐
    │                             │
    │ Anomaly = TRUE              │ Anomaly = FALSE
    │                             │
    ↓                             ↓
    Retriever                     No LLM
    ↓                             ↓
    Manual Context                Normal / No Maintenance
    ↓
    LLM
    ↓
    Maintenance Suggestion
    ↓
    Final Clean Report

IMPORTANT:
- Only statistically anomalous parameters invoke the LLM.
- Normal parameters NEVER invoke the LLM.
- Manual threshold classification is deterministic.
- LLM receives analytics + retrieved maintenance context.
- Chapter numbers, page numbers and source locations are hidden
  from the final output.
"""

import json
from typing import Any

from src.analytics import run_analytics
from src.retriever import (
    retrieve_parameter_context,
    classify_value,
)
from src.llm import analyze_parameter_with_llm


# ============================================================================
# HELPERS
# ============================================================================

def model_to_dict(obj: Any) -> dict:
    """
    Convert Pydantic model / dict into a normal dictionary.
    """

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    if hasattr(obj, "model_dump"):
        return obj.model_dump()

    if hasattr(obj, "dict"):
        return obj.dict()

    return {}


def clean_manual_context(context: dict) -> dict:
    """
    Remove source/location/chapter information before displaying
    or sending unnecessary metadata.

    The actual maintenance content is preserved.
    """

    if not isinstance(context, dict):
        return {}

    cleaned = {}

    for key, value in context.items():

        # Hide explicit source/location metadata
        if key.lower() in {
            "source",
            "sources",
            "location",
            "page",
            "pages",
            "chapter",
            "chapter_id",
            "section",
            "section_id",
            "document",
            "document_id",
            "file",
            "file_name",
        }:
            continue

        cleaned[key] = value

    return cleaned


def get_normal_range(
    manual_classification: dict,
    manual_context: dict,
):
    """
    Get normal range from the retriever.

    First preference:
        classify_value()

    Fallback:
        thresholds returned by retrieve_parameter_context()
    """

    normal_range = manual_classification.get(
        "normal_range"
    )

    if normal_range:
        return normal_range

    thresholds = manual_context.get(
        "thresholds"
    )

    if isinstance(thresholds, dict):

        normal_min = thresholds.get(
            "normal_min"
        )

        normal_max = thresholds.get(
            "normal_max"
        )

        if (
            normal_min is not None
            and normal_max is not None
        ):
            return [
                normal_min,
                normal_max,
            ]

    return None


# ============================================================================
# ANALYZE ONE PARAMETER
# ============================================================================

def process_parameter(
    parameter: str,
    analytics_obj: Any,
):
    """
    Process one parameter.

    LLM is called ONLY when statistical_anomaly == True.
    """

    analytics = model_to_dict(
        analytics_obj
    )

    current_value = analytics.get(
        "latest_value"
    )

    # ========================================================================
    # RETRIEVE MANUAL CONTEXT
    # ========================================================================

    manual_context = retrieve_parameter_context(
        parameter
    )

    # Unknown parameter
    if "error" in manual_context:

        return {
            "parameter": parameter,
            "display_name": parameter,
            "unit": None,
            "analytics": analytics,
            "normal_range": None,
            "manual_status": "UNKNOWN",
            "manual_evidence_available": False,
            "maintenance": {
                "maintenance_required": False,
                "priority": "LOW",
                "recommended_action": "",
                "reasoning": (
                    "No maintenance-manual evidence "
                    "was found for this parameter."
                ),
                "failure_modes": [],
                "confidence": "LOW",
            },
        }

    # ========================================================================
    # MANUAL CLASSIFICATION
    # ========================================================================

    manual_classification = classify_value(
        parameter,
        current_value
    )

    normal_range = get_normal_range(
        manual_classification,
        manual_context
    )

    # ========================================================================
    # GET DISPLAY INFORMATION
    # ========================================================================

    thresholds = manual_context.get(
        "thresholds",
        {}
    )

    if not isinstance(thresholds, dict):
        thresholds = {}

    display_name = (
        manual_classification.get(
            "display_name"
        )
        or thresholds.get(
            "display_name"
        )
        or parameter
    )

    unit = (
        manual_classification.get(
            "unit"
        )
        or thresholds.get(
            "unit"
        )
    )

    manual_status = (
        manual_classification.get(
            "status"
        )
        or "UNKNOWN"
    )

    # ========================================================================
    # IMPORTANT:
    #
    # ONLY STATISTICAL ANOMALIES CALL THE LLM
    # ========================================================================

    statistical_anomaly = bool(
        analytics.get(
            "statistical_anomaly",
            False
        )
    )

    # ========================================================================
    # ANOMALOUS PARAMETER
    # ========================================================================

    if statistical_anomaly:

        print(
            f"\n[LLM] Anomalous parameter detected: "
            f"{parameter}"
        )

        # ---------------------------------------------------------------
        # Remove unnecessary source/location metadata
        # ---------------------------------------------------------------

        clean_context = clean_manual_context(
            manual_context
        )

        # ---------------------------------------------------------------
        # LLM gets:
        #
        # 1. Analytics
        # 2. Manual classification
        # 3. Retrieved maintenance context
        #
        # This is the actual RAG maintenance decision.
        # ---------------------------------------------------------------

        maintenance = analyze_parameter_with_llm(
            parameter=parameter,
            analytics=analytics,
            manual_classification=manual_classification,
            manual_context=clean_context,
        )

        maintenance = model_to_dict(
            maintenance
        )

        # ---------------------------------------------------------------
        # Safety
        # ---------------------------------------------------------------

        maintenance["maintenance_required"] = True

        if not maintenance.get(
            "priority"
        ):
            maintenance["priority"] = "HIGH"

    # ========================================================================
    # NORMAL PARAMETER
    # ========================================================================

    else:

        print(
            f"\n[NO LLM] Normal parameter: "
            f"{parameter}"
        )

        maintenance = {
            "maintenance_required": False,
            "priority": "LOW",
            "recommended_action": "",
            "reasoning": (
                f"The current {display_name} value is "
                f"{current_value} {unit or ''}. "
                f"The statistical analysis shows "
                f"{analytics.get('statistical_status', 'NORMAL')} "
                f"and no statistical anomaly was detected. "
                f"No maintenance is required."
            ),
            "failure_modes": [],
            "confidence": "HIGH",
        }

    # ========================================================================
    # FINAL PARAMETER RESULT
    # ========================================================================

    return {
        "parameter": parameter,
        "display_name": display_name,
        "unit": unit,

        # Analytics result
        "analytics": analytics,

        # Manual result
        "normal_range": normal_range,
        "manual_status": manual_status,
        "manual_evidence_available": (
            manual_classification.get(
                "manual_evidence_available",
                True
            )
        ),

        # Maintenance / LLM result
        "maintenance": maintenance,
    }


# ============================================================================
# BUILD AIRCRAFT RESULT
# ============================================================================

def build_aircraft_result(
    aircraft_id: str
):
    """
    Run complete maintenance analysis for one aircraft.
    """

    # ========================================================================
    # RUN ANALYTICS
    # ========================================================================

    analytics_results = run_analytics(
        aircraft_id
    )

    if not analytics_results:

        raise ValueError(
            f"No analytics results found for aircraft "
            f"'{aircraft_id}'."
        )

    parameters = []

    # ========================================================================
    # PROCESS EVERY PARAMETER
    # ========================================================================

    for parameter, analytics_obj in analytics_results.items():

        result = process_parameter(
            parameter=parameter,
            analytics_obj=analytics_obj,
        )

        parameters.append(
            result
        )

    # ========================================================================
    # AIRCRAFT SUMMARY
    # ========================================================================

    # Get risk score and RUL from analytics
    risk_score = None
    remaining_useful_life = None

    for item in parameters:

        if item["parameter"] == "Risk_Score_(%)":

            risk_score = item[
                "analytics"
            ].get(
                "latest_value"
            )

        elif item["parameter"] == "Remaining_Useful_Life_(cycles)":

            remaining_useful_life = item[
                "analytics"
            ].get(
                "latest_value"
            )

    # Count anomalies
    anomalies_detected = sum(
        1
        for item in parameters
        if item["analytics"].get(
            "statistical_anomaly",
            False
        )
    )

    # Count maintenance decisions
    maintenance_required_count = sum(
        1
        for item in parameters
        if item["maintenance"].get(
            "maintenance_required",
            False
        )
    )

    # Overall status
    if maintenance_required_count > 0:

        overall_status = "Maintenance Due"

    else:

        overall_status = "Normal"

    return {
        "aircraft": {
            "aircraft_id": aircraft_id,

            # Flight cycle may not be present in analytics.
            "flight_cycle": None,

            "risk_score": risk_score,

            "remaining_useful_life":
                remaining_useful_life,

            "overall_status":
                overall_status,

            "parameters_analyzed":
                len(parameters),

            "anomalies_detected":
                anomalies_detected,

            "maintenance_required_count":
                maintenance_required_count,
        },

        "parameters": parameters,
    }


# ============================================================================
# CLEAN FINAL REPORT
# ============================================================================

def format_number(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.2f}"

    except (
        TypeError,
        ValueError
    ):
        return str(value)


def print_final_report(
    result: dict
):
    """
    Print clean final maintenance report.

    No:
        - Chapter
        - Page
        - Location
        - Source
        - Internal retrieval metadata
    """

    print("\n")
    print("=" * 100)
    print(
        "                 AIRCRAFT MAINTENANCE REPORT"
    )
    print("=" * 100)

    aircraft = result.get(
        "aircraft",
        {}
    )

    print(
        f"\nAircraft ID              : "
        f"{aircraft.get('aircraft_id', 'N/A')}"
    )

    print(
        f"Overall Status           : "
        f"{aircraft.get('overall_status', 'N/A')}"
    )

    print(
        f"Risk Score               : "
        f"{format_number(aircraft.get('risk_score'))}"
    )

    print(
        f"Remaining Useful Life    : "
        f"{format_number(aircraft.get('remaining_useful_life'))} cycles"
    )

    print(
        f"Parameters Analyzed      : "
        f"{aircraft.get('parameters_analyzed', 0)}"
    )

    print(
        f"Statistical Anomalies    : "
        f"{aircraft.get('anomalies_detected', 0)}"
    )

    print(
        f"Maintenance Required     : "
        f"{aircraft.get('maintenance_required_count', 0)}"
    )

    print("\n")
    print("=" * 100)
    print(
        "                    PARAMETER RESULTS"
    )
    print("=" * 100)

    for item in result.get(
        "parameters",
        []
    ):

        analytics = item.get(
            "analytics",
            {}
        )

        historical = analytics.get(
            "historical",
            {}
        )

        maintenance = item.get(
            "maintenance",
            {}
        )

        print("\n")
        print("-" * 100)

        print(
            f"PARAMETER: "
            f"{item.get('display_name', item.get('parameter'))}"
        )

        print("-" * 100)

        # ====================================================================
        # CURRENT READING
        # ====================================================================

        print(
            f"Current Value             : "
            f"{format_number(analytics.get('latest_value'))} "
            f"{item.get('unit') or ''}"
        )

        # ====================================================================
        # NORMAL RANGE
        # ====================================================================

        normal_range = item.get(
            "normal_range"
        )

        if (
            isinstance(normal_range, list)
            and len(normal_range) == 2
        ):

            print(
                f"Normal Range              : "
                f"{normal_range[0]} - "
                f"{normal_range[1]} "
                f"{item.get('unit') or ''}"
            )

        else:

            print(
                "Normal Range              : "
                "Not available"
            )

        # ====================================================================
        # HISTORICAL ANALYTICS
        # ====================================================================

        print(
            f"Historical Mean           : "
            f"{format_number(historical.get('mean'))}"
        )

        print(
            f"Historical Median         : "
            f"{format_number(historical.get('median'))}"
        )

        print(
            f"Historical Std            : "
            f"{format_number(historical.get('std'))}"
        )

        print(
            f"Difference from Mean      : "
            f"{format_number(analytics.get('difference_from_mean'))}"
        )

        percentage_change = analytics.get(
            "percentage_change"
        )

        if percentage_change is not None:

            print(
                f"Percentage Change         : "
                f"{format_number(percentage_change)}%"
            )

        else:

            print(
                "Percentage Change         : N/A"
            )

        print(
            f"Z-Score                   : "
            f"{format_number(analytics.get('z_score'))}"
        )

        print(
            f"Trend                     : "
            f"{analytics.get('trend', 'N/A')}"
        )

        print(
            f"Statistical Status        : "
            f"{analytics.get('statistical_status', 'N/A')}"
        )

        # ====================================================================
        # MANUAL STATUS
        # ====================================================================

        print(
            f"Manual Status             : "
            f"{item.get('manual_status', 'UNKNOWN')}"
        )

        # ====================================================================
        # MAINTENANCE
        # ====================================================================

        required = maintenance.get(
            "maintenance_required",
            False
        )

        print(
            f"Maintenance Required      : "
            f"{'YES' if required else 'NO'}"
        )

        print(
            f"Priority                  : "
            f"{maintenance.get('priority', 'LOW')}"
        )

        # ====================================================================
        # MAINTENANCE SUGGESTION
        # ====================================================================

        action = maintenance.get(
            "recommended_action"
        )

        if action:

            print(
                f"Maintenance Suggestion    : "
                f"{action}"
            )

        else:

            print(
                "Maintenance Suggestion    : "
                "No maintenance action required."
            )

        # ====================================================================
        # REASONING
        # ====================================================================

        reasoning = maintenance.get(
            "reasoning"
        )

        if reasoning:

            print(
                f"Reasoning                 : "
                f"{reasoning}"
            )

        # ====================================================================
        # FAILURE MODES
        # ====================================================================

        failure_modes = maintenance.get(
            "failure_modes",
            []
        )

        if failure_modes:

            print(
                "Relevant Failure Modes   :"
            )

            for failure in failure_modes:

                if isinstance(
                    failure,
                    dict
                ):

                    name = failure.get(
                        "name"
                    )

                    if name:
                        print(
                            f"  - {name}"
                        )

                else:

                    print(
                        f"  - {failure}"
                    )

        else:

            print(
                "Relevant Failure Modes   : "
                "None identified"
            )

        print("-" * 100)

    print("\n")
    print("=" * 100)
    print(
        "                       END OF REPORT"
    )
    print("=" * 100)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    # Change aircraft here when testing
    AIRCRAFT_ID = "AIR-001"

    print("\n")
    print("=" * 100)
    print(
        "Starting Aircraft Maintenance Intelligence Pipeline"
    )
    print("=" * 100)

    try:

        final_result = build_aircraft_result(
            AIRCRAFT_ID
        )

        # ====================================================================
        # CLEAN HUMAN-READABLE OUTPUT
        # ====================================================================

        print_final_report(
            final_result
        )

        # ====================================================================
        # OPTIONAL JSON OUTPUT
        # ====================================================================
        #
        # Uncomment if you want the dashboard/API to consume JSON.
        #
        # print(
        #     json.dumps(
        #         final_result,
        #         indent=4,
        #         ensure_ascii=False,
        #         default=str
        #     )
        # )

    except Exception as exc:

        print("\n")
        print("=" * 100)
        print("ERROR")
        print("=" * 100)

        print(
            f"\n{type(exc).__name__}: {exc}"
        )

        raise