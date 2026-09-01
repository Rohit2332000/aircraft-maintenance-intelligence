from typing import Any

from src.retriever import retrieve_parameter_context


# ============================================================
# CLASSIFY VALUE AGAINST MAINTENANCE MANUAL
# ============================================================

def classify_value(
    parameter_id_or_alias: str,
    value: float,
) -> dict[str, Any]:
    """
    Classify a parameter value using the thresholds
    returned by the existing maintenance-manual retriever.

    No LLM or statistical analysis is used here.
    """

    # --------------------------------------------------------
    # Retrieve complete manual context
    # --------------------------------------------------------

    context = retrieve_parameter_context(
        parameter_id_or_alias
    )

    # --------------------------------------------------------
    # Unknown parameter
    # --------------------------------------------------------

    if "error" in context:
        return {
            "parameter_id": parameter_id_or_alias,
            "value": value,
            "status": "UNKNOWN",
            "manual_evidence_available": False,
            "reason": context["error"],
        }

    # --------------------------------------------------------
    # Extract parameter information
    # --------------------------------------------------------

    parameter_id = context.get(
        "parameter_id",
        parameter_id_or_alias,
    )

    band = context.get(
        "thresholds"
    )

    # --------------------------------------------------------
    # No threshold information
    # --------------------------------------------------------

    if not band:
        return {
            "parameter_id": parameter_id,
            "value": value,
            "status": "UNKNOWN",
            "manual_evidence_available": False,
            "reason": (
                "No threshold information "
                "is available in the maintenance manual."
            ),
        }

    # --------------------------------------------------------
    # Extract threshold configuration
    # --------------------------------------------------------

    direction = band.get(
        "critical_direction"
    )

    normal_min = band.get(
        "normal_min"
    )

    normal_max = band.get(
        "normal_max"
    )

    warning_min = band.get(
        "warning_min"
    )

    warning_max = band.get(
        "warning_max"
    )

    critical_min = band.get(
        "critical_min"
    )

    critical_max = band.get(
        "critical_max"
    )

    # --------------------------------------------------------
    # Default status
    # --------------------------------------------------------

    status = "Normal"

    # ========================================================
    # CRITICAL DIRECTION: ABOVE
    # ========================================================

    if direction == "above":

        if (
            critical_min is not None
            and value > critical_min
        ):
            status = "Critical"

        elif (
            warning_min is not None
            and value > warning_min
        ):
            status = "Warning"

    # ========================================================
    # CRITICAL DIRECTION: BELOW
    # ========================================================

    elif direction == "below":

        if (
            critical_max is not None
            and value < critical_max
        ):
            status = "Critical"

        elif (
            warning_max is not None
            and value < warning_max
        ):
            status = "Warning"

    # ========================================================
    # OUTSIDE NORMAL BAND
    # ========================================================

    elif direction == "outside_band":

        if (
            normal_min is not None
            and normal_max is not None
        ):
            if not (
                normal_min
                <= value
                <= normal_max
            ):
                status = "Warning"

    # ========================================================
    # UNKNOWN / FALLBACK
    # ========================================================

    else:

        if (
            normal_min is not None
            and normal_max is not None
        ):
            if not (
                normal_min
                <= value
                <= normal_max
            ):
                status = "Warning"

    # --------------------------------------------------------
    # Return structured classification
    # --------------------------------------------------------

    return {
        "parameter_id": parameter_id,
        "display_name": band.get(
            "display_name"
        ),
        "value": value,
        "unit": band.get(
            "unit"
        ),
        "status": status,
        "normal_range": (
            [normal_min, normal_max]
            if (
                normal_min is not None
                and normal_max is not None
            )
            else None
        ),
        "recommended_action": band.get(
            "recommended_action"
        ),
        "source": band.get(
            "source"
        ),
        "manual_evidence_available": True,
    }


# ============================================================
# CLASSIFY FROM ANALYTICS RESULT
# ============================================================

def classify_analytics_result(
    parameter_id_or_alias: str,
    analytics_result: Any,
) -> dict[str, Any]:
    """
    Classify the latest value contained in AnalyticsResult.
    """

    latest_value = analytics_result.latest_value

    if latest_value is None:
        return {
            "parameter_id": parameter_id_or_alias,
            "status": "NO_DATA",
            "manual_evidence_available": False,
            "reason": (
                "Latest parameter value "
                "is unavailable."
            ),
        }

    return classify_value(
        parameter_id_or_alias=parameter_id_or_alias,
        value=latest_value,
    )