
# -*- coding: utf-8 -*-

"""
Aircraft Maintenance LangGraph

FLOW
----

                    AIRCRAFT ID
                         |
                         v
                  +-------------+
                  |  ANALYTICS  |
                  +-------------+
                         |
                         v
             Analytics for every parameter
                         |
                         v
              +-----------------------+
              | Maintenance Processing|
              +-----------------------+
                    /           \
                   /             \
          NORMAL /                 \ ANOMALOUS
                /                   \
               v                     v
       Manual classification    Retriever context
       Normal range             + Analytics data
               |                     |
               |                     v
               |                   LLM
               |                     |
               v                     v
       No LLM call          Maintenance suggestion
                \                   /
                 \                 /
                  v               v
                 +----------------+
                 | FINAL RESPONSE |
                 +----------------+

IMPORTANT
---------
1. Analytics is calculated for ALL monitored parameters.
2. Manual normal-range information is added where available.
3. ONLY statistical anomalies invoke the LLM.
4. Normal parameters NEVER invoke the LLM.
5. LLM receives analytics + retrieved maintenance context.
6. Final response does not expose chapter/location/source information.
7. file_path is NOT required.
"""

from typing import Any, TypedDict
import json

from langgraph.graph import StateGraph, END

from src.analytics import run_aircraft_analytics
from src.retriever import (
    resolve_parameter_id,
    retrieve_parameter_context,
    classify_value,
)
from src.llm import analyze_parameter_with_llm


# ============================================================================
# GRAPH STATE
# ============================================================================

class MaintenanceState(TypedDict, total=False):
    aircraft_id: str

    # Optional dataframe.
    # If omitted, analytics.py loads the dataset itself.
    df: Any

    # Raw analytics result
    analytics: dict

    # Final parameter results
    parameters: list

    # Aircraft-level summary
    aircraft: dict

    # Final response
    result: dict

    # Error
    error: str


# ============================================================================
# HELPERS
# ============================================================================

def _to_dict(value: Any) -> Any:
    """
    Convert Pydantic/dataclass/object values into normal Python dictionaries.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {
            key: _to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _to_dict(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _to_dict(item)
            for item in value
        ]

    # Pydantic v2
    if hasattr(value, "model_dump"):
        try:
            return _to_dict(
                value.model_dump()
            )
        except Exception:
            pass

    # Pydantic v1
    if hasattr(value, "dict"):
        try:
            return _to_dict(
                value.dict()
            )
        except Exception:
            pass

    # Dataclass
    if hasattr(value, "__dataclass_fields__"):
        try:
            from dataclasses import asdict

            return _to_dict(
                asdict(value)
            )
        except Exception:
            pass

    return value


def _safe_float(value: Any):
    """
    Convert numeric values safely.
    """

    if value is None:
        return None

    try:
        return float(value)
    except Exception:
        return value


def _clean_sources(value: Any) -> list:
    """
    Do not expose manual chapter/location/source information
    in the final API response.

    The manual context is still sent to the LLM.
    """

    if not isinstance(value, list):
        return []

    return []


def _clean_maintenance_output(
    maintenance: dict,
) -> dict:
    """
    Keep only user-facing maintenance information.

    Chapter/location/source references are intentionally removed.
    """

    if not isinstance(maintenance, dict):
        return {
            "maintenance_required": False,
            "priority": "LOW",
            "recommended_action": "",
            "reasoning": "",
            "failure_modes": [],
            "confidence": "LOW",
            "manual_sources": [],
        }

    return {
        "maintenance_required": bool(
            maintenance.get(
                "maintenance_required",
                False,
            )
        ),

        "priority": (
            maintenance.get("priority")
            or "LOW"
        ),

        "recommended_action": (
            maintenance.get(
                "recommended_action"
            )
            or ""
        ),

        "reasoning": (
            maintenance.get(
                "reasoning"
            )
            or ""
        ),

        "failure_modes": (
            maintenance.get(
                "failure_modes"
            )
            if isinstance(
                maintenance.get("failure_modes"),
                list,
            )
            else []
        ),

        "confidence": (
            maintenance.get(
                "confidence"
            )
            or "MEDIUM"
        ),

        # Intentionally empty.
        "manual_sources": [],
    }


# ============================================================================
# MANUAL INFORMATION
# ============================================================================

def _get_manual_information(
    parameter: str,
    current_value: Any,
) -> tuple[dict, dict]:
    """
    Retrieve maintenance-manual information and deterministic
    threshold classification.

    This function does NOT call the LLM.
    """

    # ------------------------------------------------------------------------
    # Resolve Excel parameter -> canonical parameter ID
    # ------------------------------------------------------------------------

    parameter_id = resolve_parameter_id(
        parameter
    )

    # ------------------------------------------------------------------------
    # Unknown parameter
    # ------------------------------------------------------------------------

    if parameter_id is None:
        return (
            {
                "error": f"Unknown parameter: {parameter}",
            },
            {
                "parameter_id": parameter,
                "value": current_value,
                "status": "UNKNOWN",
                "manual_evidence_available": False,
            },
        )

    # ------------------------------------------------------------------------
    # Retrieve complete manual context
    # ------------------------------------------------------------------------

    manual_context = retrieve_parameter_context(
        parameter_id
    )

    # ------------------------------------------------------------------------
    # Deterministic threshold classification
    # ------------------------------------------------------------------------

    try:
        numeric_value = float(
            current_value
        )
    except Exception:
        numeric_value = None

    if numeric_value is not None:
        manual_classification = classify_value(
            parameter_id,
            numeric_value,
        )
    else:
        manual_classification = {
            "parameter_id": parameter_id,
            "value": current_value,
            "status": "UNKNOWN",
            "manual_evidence_available": False,
            "reason": "Current value is not numeric.",
        }

    return (
        _to_dict(manual_context),
        _to_dict(manual_classification),
    )


# ============================================================================
# NORMAL RANGE
# ============================================================================

def _extract_normal_range(
    manual_context: dict,
    manual_classification: dict,
):
    """
    Extract the maintenance-manual normal range.

    Priority:
        1. classify_value()
        2. thresholds in retrieve_parameter_context()
    """

    # ------------------------------------------------------------------------
    # First source: deterministic classifier
    # ------------------------------------------------------------------------

    normal_range = manual_classification.get(
        "normal_range"
    )

    if (
        isinstance(normal_range, list)
        and len(normal_range) == 2
    ):
        return normal_range

    # ------------------------------------------------------------------------
    # Second source: manual threshold object
    # ------------------------------------------------------------------------

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
# ANALYTICS NODE
# ============================================================================

def analytics_node(
    state: MaintenanceState,
) -> dict:

    aircraft_id = state.get(
        "aircraft_id"
    )

    if not aircraft_id:
        raise ValueError(
            "aircraft_id is required."
        )

    # ------------------------------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT require file_path.
    #
    # analytics.py already supports:
    #
    # run_aircraft_analytics(
    #     aircraft_id,
    #     df=None
    # )
    # ------------------------------------------------------------------------

    df = state.get(
        "df"
    )

    if df is not None:
        analytics_result = run_aircraft_analytics(
            aircraft_id=aircraft_id,
            df=df,
        )
    else:
        analytics_result = run_aircraft_analytics(
            aircraft_id=aircraft_id
        )

    analytics_result = _to_dict(
        analytics_result
    )

    return {
        "analytics": analytics_result,
    }


# ============================================================================
# MAINTENANCE NODE
# ============================================================================

def maintenance_node(
    state: MaintenanceState,
) -> dict:

    analytics = state.get(
        "analytics",
        {},
    )

    if not analytics:
        return {
            "parameters": [],
        }

    parameters = []

    # ========================================================================
    # PROCESS EVERY PARAMETER
    # ========================================================================

    for parameter, analytics_obj in analytics.items():

        analytics_data = _to_dict(
            analytics_obj
        )

        if not isinstance(
            analytics_data,
            dict,
        ):
            analytics_data = {}

        # --------------------------------------------------------------------
        # Current value
        # --------------------------------------------------------------------

        current_value = analytics_data.get(
            "latest_value"
        )

        # --------------------------------------------------------------------
        # Retrieve maintenance-manual information
        #
        # This does NOT call the LLM.
        # --------------------------------------------------------------------

        manual_context, manual_classification = (
            _get_manual_information(
                parameter=parameter,
                current_value=current_value,
            )
        )

        # --------------------------------------------------------------------
        # Normal range
        # --------------------------------------------------------------------

        normal_range = _extract_normal_range(
            manual_context=manual_context,
            manual_classification=manual_classification,
        )

        # --------------------------------------------------------------------
        # Statistical anomaly
        # --------------------------------------------------------------------

        statistical_anomaly = bool(
            analytics_data.get(
                "statistical_anomaly",
                False,
            )
        )

        # --------------------------------------------------------------------
        # ================================================================
        # NORMAL PARAMETER
        # ================================================================
        #
        # NO LLM CALL.
        #
        # --------------------------------------------------------------------

        if not statistical_anomaly:

            maintenance = {
                "maintenance_required": False,
                "priority": "LOW",
                "recommended_action": "",
                "reasoning": (
                    f"The current {parameter} value is "
                    f"{current_value}. "
                    f"The statistical status is "
                    f"{analytics_data.get('statistical_status', 'NORMAL')} "
                    f"and no statistical anomaly was detected. "
                    f"No maintenance is required."
                ),
                "failure_modes": [],
                "confidence": "HIGH",
                "manual_sources": [],
            }

        # --------------------------------------------------------------------
        # ================================================================
        # ANOMALOUS PARAMETER
        # ================================================================
        #
        # ONLY HERE DO WE CALL THE LLM.
        #
        # --------------------------------------------------------------------

        else:

            print(
                f"\n[LLM] Processing anomalous parameter: "
                f"{parameter}"
            )

            # ---------------------------------------------------------------
            # Build complete maintenance data for LLM
            # ---------------------------------------------------------------

            llm_maintenance_data = {
                "parameter": parameter,

                "current_value": current_value,

                "analytics": analytics_data,

                "normal_range": normal_range,

                "manual_classification": (
                    manual_classification
                ),

                "maintenance_manual": {
                    "thresholds": (
                        manual_context.get(
                            "thresholds"
                        )
                    ),

                    "sensor": (
                        manual_context.get(
                            "sensor",
                            [],
                        )
                    ),

                    "failure_modes": (
                        manual_context.get(
                            "failure_modes",
                            [],
                        )
                    ),

                    "procedures": (
                        manual_context.get(
                            "procedures",
                            [],
                        )
                    ),

                    "inspection_intervals": (
                        manual_context.get(
                            "inspection_intervals",
                            [],
                        )
                    ),

                    "troubleshooting_tree": (
                        manual_context.get(
                            "troubleshooting_tree",
                            [],
                        )
                    ),
                },
            }

            # ---------------------------------------------------------------
            # Send analytics + retrieved manual context to LLM
            #
            # analyze_parameter_with_llm() internally uses
            # build_parameter_prompt().
            # ---------------------------------------------------------------

            try:

                maintenance_result = (
                    analyze_parameter_with_llm(
                        parameter=parameter,

                        analytics=analytics_data,

                        manual_classification=(
                            manual_classification
                        ),

                        manual_context=(
                            llm_maintenance_data
                        ),
                    )
                )

                maintenance = _clean_maintenance_output(
                    _to_dict(
                        maintenance_result
                    )
                )

            except Exception as exc:

                print(
                    f"\n[LLM ERROR] {parameter}: {exc}"
                )

                # -----------------------------------------------------------
                # The llm.py already has its own deterministic fallback.
                #
                # This is an additional graph-level protection.
                # -----------------------------------------------------------

                maintenance = {
                    "maintenance_required": True,
                    "priority": "HIGH",
                    "recommended_action": (
                        manual_classification.get(
                            "recommended_action"
                        )
                        or ""
                    ),
                    "reasoning": (
                        "A statistical anomaly was detected. "
                        "The maintenance recommendation could not "
                        "be generated by the LLM."
                    ),
                    "failure_modes": [],
                    "confidence": "LOW",
                    "manual_sources": [],
                }

        # ====================================================================
        # BUILD PARAMETER RESULT
        # ====================================================================

        parameter_result = {
            "parameter": parameter,

            "display_name": (
                manual_classification.get(
                    "display_name"
                )
                or parameter.replace(
                    "_",
                    " ",
                )
            ),

            "unit": (
                manual_classification.get(
                    "unit"
                )
            ),

            # ---------------------------------------------------------------
            # ANALYTICS
            # ---------------------------------------------------------------

            "analytics": analytics_data,

            # ---------------------------------------------------------------
            # MANUAL NORMAL RANGE
            # ---------------------------------------------------------------

            "normal_range": normal_range,

            # ---------------------------------------------------------------
            # MANUAL CLASSIFICATION
            # ---------------------------------------------------------------

            "manual_status": (
                manual_classification.get(
                    "status"
                )
            ),

            "manual_evidence_available": (
                manual_classification.get(
                    "manual_evidence_available",
                    False,
                )
            ),

            # ---------------------------------------------------------------
            # MAINTENANCE / LLM RESULT
            # ---------------------------------------------------------------

            "maintenance": maintenance,
        }

        parameters.append(
            parameter_result
        )

    return {
        "parameters": parameters,
    }


# ============================================================================
# FINAL NODE
# ============================================================================

def final_node(
    state: MaintenanceState,
) -> dict:

    aircraft_id = state.get(
        "aircraft_id"
    )

    parameters = state.get(
        "parameters",
        [],
    )

    # ========================================================================
    # AIRCRAFT SUMMARY
    # ========================================================================

    anomalies_detected = 0
    maintenance_required_count = 0

    risk_score = None
    remaining_useful_life = None
    flight_cycle = None

    for item in parameters:

        analytics = item.get(
            "analytics",
            {},
        )

        # ---------------------------------------------------------------
        # Anomaly count
        # ---------------------------------------------------------------

        if analytics.get(
            "statistical_anomaly",
            False,
        ):
            anomalies_detected += 1

        # ---------------------------------------------------------------
        # Maintenance count
        # ---------------------------------------------------------------

        maintenance = item.get(
            "maintenance",
            {},
        )

        if maintenance.get(
            "maintenance_required",
            False,
        ):
            maintenance_required_count += 1

        # ---------------------------------------------------------------
        # Risk score
        # ---------------------------------------------------------------

        if (
            item.get("parameter")
            == "Risk_Score_(%)"
        ):
            risk_score = analytics.get(
                "latest_value"
            )

        # ---------------------------------------------------------------
        # Remaining useful life
        # ---------------------------------------------------------------

        if (
            item.get("parameter")
            == "Remaining_Useful_Life_(cycles)"
        ):
            remaining_useful_life = analytics.get(
                "latest_value"
            )

        # ---------------------------------------------------------------
        # Flight cycle is normally not a monitored parameter.
        #
        # If available in state df, obtain it.
        # ---------------------------------------------------------------

    # ========================================================================
    # DETERMINE OVERALL STATUS
    # ========================================================================

    if maintenance_required_count > 0:

        overall_status = "Maintenance Due"

    elif anomalies_detected > 0:

        overall_status = "Attention Required"

    else:

        overall_status = "Normal"

    # ========================================================================
    # FINAL AIRCRAFT RESULT
    # ========================================================================

    aircraft_summary = {
        "aircraft_id": aircraft_id,

        "flight_cycle": flight_cycle,

        "risk_score": _safe_float(
            risk_score
        ),

        "remaining_useful_life": _safe_float(
            remaining_useful_life
        ),

        "overall_status": overall_status,

        "parameters_analyzed": len(
            parameters
        ),

        "anomalies_detected": (
            anomalies_detected
        ),

        "maintenance_required_count": (
            maintenance_required_count
        ),
    }

    # ========================================================================
    # FINAL RESULT
    # ========================================================================

    final_result = {
        "aircraft": aircraft_summary,

        "parameters": parameters,
    }

    return {
        "aircraft": aircraft_summary,
        "result": final_result,
    }


# ============================================================================
# ERROR NODE
# ============================================================================

def error_node(
    state: MaintenanceState,
) -> dict:

    return {
        "result": {
            "error": state.get(
                "error",
                "Unknown error.",
            )
        }
    }


# ============================================================================
# BUILD GRAPH
# ============================================================================

def build_maintenance_graph():

    graph = StateGraph(
        MaintenanceState
    )

    # ------------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------------

    graph.add_node(
        "analytics",
        analytics_node,
    )

    graph.add_node(
        "maintenance",
        maintenance_node,
    )

    graph.add_node(
        "final",
        final_node,
    )

    # ------------------------------------------------------------------------
    # Edges
    # ------------------------------------------------------------------------

    graph.set_entry_point(
        "analytics"
    )

    graph.add_edge(
        "analytics",
        "maintenance",
    )

    graph.add_edge(
        "maintenance",
        "final",
    )

    graph.add_edge(
        "final",
        END,
    )

    return graph.compile()


# ============================================================================
# GLOBAL GRAPH INSTANCE
# ============================================================================

maintenance_graph = (
    build_maintenance_graph()
)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def run_maintenance_analysis(
    aircraft_id: str,
    df=None,
) -> dict:
    """
    Run complete aircraft maintenance analysis.

    Parameters
    ----------
    aircraft_id:
        Aircraft identifier, e.g. "AIR-001"

    df:
        Optional pandas DataFrame.

        If omitted, analytics.py loads the configured dataset.

    Returns
    -------
    dict
        Complete analytics + maintenance result.
    """

    state: MaintenanceState = {
        "aircraft_id": aircraft_id,
    }

    if df is not None:
        state["df"] = df

    result = maintenance_graph.invoke(
        state
    )

    return result.get(
        "result",
        result,
    )


# ============================================================================
# OPTIONAL CLI TEST
# ============================================================================

if __name__ == "__main__":

    result = run_maintenance_analysis(
        "AIR-001"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )
