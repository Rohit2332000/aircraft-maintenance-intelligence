
# -*- coding: utf-8 -*-

"""
LLM layer for Aircraft Maintenance Intelligence.

IMPORTANT:

This module is ONLY used for parameters that have been identified
as anomalous by analytics.py.

Normal parameters must NOT call this module.

Flow:

    Anomalous Parameter
            ↓
       PDF Retriever
            ↓
       ChatGroq / LLM
            ↓
    Maintenance Decision

Normal parameters are handled directly by graph.py:

    Normal Parameter
            ↓
       PDF Retriever
            ↓
    Normal-range information
            ↓
    "No maintenance required"
"""

import json
import re

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
)

from src.prompts import (
    MAINTENANCE_SYSTEM_PROMPT,
    build_parameter_prompt,
)

from src.schemas import ParameterAnalysis


# ============================================================================
# GROQ
# ============================================================================

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0,
)


# ============================================================================
# JSON EXTRACTION
# ============================================================================

def extract_json(text: str) -> dict:
    """
    Extract JSON object from the LLM response.
    """

    if not text:
        raise ValueError(
            "LLM returned an empty response."
        )

    text = text.strip()

    # Remove markdown JSON fences
    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```\s*",
        "",
        text,
    )

    text = text.strip()

    # Direct JSON parsing
    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # Find JSON object inside response
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            f"No JSON object found in LLM response:\n{text}"
        )

    json_text = text[start:end + 1]

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON returned by LLM:\n{json_text}"
        ) from exc


# ============================================================================
# DETERMINISTIC FALLBACK
# ============================================================================

def deterministic_maintenance_fallback(
    parameter: str,
    analytics: dict,
    manual_classification: dict,
    manual_context: dict,
) -> dict:
    """
    Deterministic fallback used ONLY when the LLM fails.

    This function is primarily designed for anomalous parameters.

    It never allows an anomalous parameter to silently become
    maintenance_required=False.
    """

    statistical_anomaly = bool(
        analytics.get(
            "statistical_anomaly",
            False,
        )
    )

    statistical_status = (
        analytics.get(
            "statistical_status"
        )
        or ""
    ).upper()

    manual_status = (
        manual_classification.get(
            "status"
        )
        or ""
    ).upper()

    manual_action = (
        manual_classification.get(
            "recommended_action"
        )
        or ""
    )

    # ------------------------------------------------------------------------
    # Determine priority
    # ------------------------------------------------------------------------

    if manual_status == "CRITICAL":

        maintenance_required = True
        priority = "CRITICAL"

    elif statistical_anomaly:

        maintenance_required = True

        if manual_status == "WARNING":
            priority = "HIGH"
        else:
            priority = "HIGH"

    elif manual_status == "WARNING":

        maintenance_required = True
        priority = "MEDIUM"

    else:

        maintenance_required = False
        priority = "LOW"

    # ------------------------------------------------------------------------
    # Collect manual sources
    # ------------------------------------------------------------------------

    sources = []

    source = manual_classification.get(
        "source"
    )

    if source:
        sources.append(source)

    if isinstance(manual_context, dict):

        context_sources = manual_context.get(
            "sources",
            []
        )

        if isinstance(context_sources, list):

            for item in context_sources:

                if item and item not in sources:
                    sources.append(item)

    # ------------------------------------------------------------------------
    # Reasoning
    # ------------------------------------------------------------------------

    current_value = analytics.get(
        "latest_value"
    )

    historical = analytics.get(
        "historical",
        {}
    )

    mean = (
        historical.get("mean")
        if isinstance(historical, dict)
        else None
    )

    z_score = analytics.get(
        "z_score"
    )

    if maintenance_required:

        reasoning = (
            f"Maintenance attention is required for "
            f"{parameter}. "
            f"The current value is {current_value}. "
            f"The statistical status is "
            f"{statistical_status or 'UNKNOWN'}"
        )

        if z_score is not None:
            reasoning += (
                f" with a z-score of {z_score:.2f}"
            )

        if mean is not None:
            reasoning += (
                f", compared with a historical mean "
                f"of {mean:.2f}"
            )

        reasoning += (
            f". The manual classification is "
            f"{manual_status or 'UNKNOWN'}."
        )

        if manual_action:

            reasoning += (
                f" The maintenance manual recommends: "
                f"{manual_action}."
            )

    else:

        reasoning = (
            f"No maintenance is required for "
            f"{parameter}. "
            f"The available statistical and manual "
            f"classification information does not "
            f"indicate a maintenance condition."
        )

    # ------------------------------------------------------------------------
    # Return maintenance decision
    # ------------------------------------------------------------------------

    return {
        "maintenance_required": maintenance_required,
        "priority": priority,
        "recommended_action": manual_action,
        "reasoning": reasoning,
        "failure_modes": [],
        "confidence": "MEDIUM",
        "manual_sources": sources,
    }


# ============================================================================
# ANALYZE ANOMALOUS PARAMETER WITH LLM
# ============================================================================

def analyze_parameter_with_llm(
    parameter: str,
    analytics: dict,
    manual_classification: dict,
    manual_context: dict,
) -> ParameterAnalysis:
    """
    Analyze ONE ANOMALOUS parameter using ChatGroq.

    IMPORTANT:
        graph.py should call this function ONLY when:

            analytics["statistical_anomaly"] == True

    Normal parameters should never reach this function.
    """

    # =========================================================================
    # SAFETY CHECK
    # =========================================================================

    if not analytics.get(
        "statistical_anomaly",
        False,
    ):

        raise ValueError(
            f"LLM called for non-anomalous parameter: {parameter}. "
            "Normal parameters must be handled directly by graph.py."
        )

    # =========================================================================
    # BUILD PROMPT
    # =========================================================================

    prompt = build_parameter_prompt(
        parameter=parameter,
        analytics=analytics,
        manual_classification=manual_classification,
        manual_context=manual_context,
    )

    messages = [
        SystemMessage(
            content=MAINTENANCE_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=prompt
        ),
    ]

    # =========================================================================
    # CALL GROQ
    # =========================================================================

    try:

        response = llm.invoke(
            messages
        )

        content = response.content

        if isinstance(content, list):

            content = "".join(
                str(item)
                for item in content
            )

        content = str(content)

        # =====================================================================
        # PARSE JSON
        # =====================================================================

        data = extract_json(
            content
        )

        # =====================================================================
        # VALIDATE / NORMALIZE MAINTENANCE OUTPUT
        # =====================================================================

        maintenance = {

            "maintenance_required": bool(
                data.get(
                    "maintenance_required",
                    True,
                )
            ),

            "priority": (
                data.get(
                    "priority"
                )
                or "HIGH"
            ),

            "recommended_action": (
                data.get(
                    "recommended_action"
                )
                or manual_classification.get(
                    "recommended_action"
                )
                or ""
            ),

            "reasoning": (
                data.get(
                    "reasoning"
                )
                or ""
            ),

            "failure_modes": (
                data.get(
                    "failure_modes"
                )
                or []
            ),

            "confidence": (
                data.get(
                    "confidence"
                )
                or "MEDIUM"
            ),

            "manual_sources": (
                data.get(
                    "manual_sources"
                )
                or []
            ),
        }

        # =====================================================================
        # SAFETY:
        # Anomalous parameter should not return LOW/false accidentally.
        # =====================================================================

        if analytics.get(
            "statistical_anomaly",
            False,
        ):

            if not maintenance[
                "maintenance_required"
            ]:

                maintenance[
                    "maintenance_required"
                ] = True

                if maintenance[
                    "priority"
                ] == "LOW":

                    maintenance[
                        "priority"
                    ] = "HIGH"

        # =====================================================================
        # Return ONLY maintenance object
        #
        # graph.py attaches analytics + manual data later.
        # =====================================================================

        return maintenance

    # =========================================================================
    # LLM FAILURE
    # =========================================================================

    except Exception as exc:

        print(
            f"\n[LLM WARNING] {parameter}: {exc}"
        )

        print(
            "[LLM FALLBACK] Using deterministic maintenance decision."
        )

        return deterministic_maintenance_fallback(
            parameter=parameter,
            analytics=analytics,
            manual_classification=manual_classification,
            manual_context=manual_context,
        )
