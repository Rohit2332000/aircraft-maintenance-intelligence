# -*- coding: utf-8 -*-

"""
PDF-only retriever for the AeroTech ATX-200 Maintenance Manual.

Responsibilities
----------------
1. Resolve parameter names from:
   - Canonical parameter IDs
   - Excel column names
   - Configured aliases

2. Retrieve all maintenance-manual information for a parameter:
   - Thresholds
   - Sensor information
   - Failure modes
   - Procedures
   - Troubleshooting tree

3. Classify a parameter reading using deterministic
   maintenance-manual threshold logic.

This module does NOT:
- Load Excel data
- Perform statistical analysis
- Calculate z-scores
- Calculate historical trends
- Call an LLM
- Call LangGraph
- Call FastAPI

The caller supplies the parameter and value.
"""


from typing import Optional


from src.kb_data import (
    PARAMETERS,
    PARAMETER_ALIASES,
    SENSORS,
    FAILURE_MODES,
    PROCEDURES,
    INSPECTION_INTERVALS,
    TROUBLESHOOTING_TREES,
    DECISION_MATRIX,
    GLOSSARY,
)


# ============================================================================
# EXCEL PARAMETER NAME -> CANONICAL PARAMETER ID
# ============================================================================

EXCEL_TO_PARAMETER_ID = {

    "Engine_Temperature_(°C)": "engine_temperature",

    "Exhaust_Gas_Temperature_(°C)": (
        "exhaust_gas_temperature"
    ),

    "Oil_Temperature_(°C)": (
        "oil_temperature"
    ),

    "Oil_Pressure_(PSI)": (
        "oil_pressure"
    ),

    "Fuel_Flow_(kg/hr)": (
        "fuel_flow"
    ),

    "Compressor_Pressure_(PSI)": (
        "compressor_pressure"
    ),

    "Engine_Vibration_(mm/s)": (
        "engine_vibration"
    ),

    "Hydraulic_Pressure_(PSI)": (
        "hydraulic_pressure"
    ),

    "Engine_RPM": (
        "engine_rpm"
    ),

    "Humidity_(%)": (
        "ambient_humidity"
    ),

    "Ambient_Temperature_(°C)": (
        "ambient_temperature"
    ),

    "Outside_Air_Temperature_(°C)": (
        "outside_air_temperature"
    ),
}


# ============================================================================
# LOOKUP INDEXES
# ============================================================================

# Canonical parameter ID -> parameter definition

_PARAM_BY_ID = {
    p["parameter_id"]: p
    for p in PARAMETERS
}


# Alias -> canonical parameter ID

_ALIAS_TO_ID = {}


for parameter_id, aliases in PARAMETER_ALIASES.items():

    for alias in aliases:

        _ALIAS_TO_ID[
            alias.strip().lower()
        ] = parameter_id

    # Also allow parameter ID itself
    # after replacing underscores with spaces.

    _ALIAS_TO_ID[
        parameter_id.replace("_", " ").lower()
    ] = parameter_id


# Excel column name -> canonical parameter ID

_EXCEL_TO_ID_NORMALIZED = {
    excel_name.strip().lower(): parameter_id
    for excel_name, parameter_id
    in EXCEL_TO_PARAMETER_ID.items()
}


# ============================================================================
# PARAMETER RESOLUTION
# ============================================================================

def resolve_parameter_id(
    text: str,
) -> Optional[str]:
    """
    Resolve a parameter into its canonical parameter ID.

    Supported input formats:

        oil_pressure

        "oil pressure"

        "Oil_Pressure_(PSI)"

        configured aliases such as:
        "oil PSI"
        "oil pressure"
        etc.

    Returns:
        Canonical parameter ID or None.
    """

    if not text:
        return None

    key = str(text).strip().lower()

    # ------------------------------------------------------------------------
    # 1. Already canonical parameter ID
    # ------------------------------------------------------------------------

    if key in _PARAM_BY_ID:
        return key

    # ------------------------------------------------------------------------
    # 2. Excel column name
    # ------------------------------------------------------------------------

    if key in _EXCEL_TO_ID_NORMALIZED:
        return _EXCEL_TO_ID_NORMALIZED[key]

    # ------------------------------------------------------------------------
    # 3. Existing configured aliases
    # ------------------------------------------------------------------------

    if key in _ALIAS_TO_ID:
        return _ALIAS_TO_ID[key]

    # ------------------------------------------------------------------------
    # 4. Normalized Excel fallback
    #
    # Handles small formatting differences such as:
    #
    # Oil_Pressure_(PSI)
    # oil_pressure_(psi)
    # ------------------------------------------------------------------------

    normalized_key = (
        key
        .replace(" ", "_")
    )

    if normalized_key in _EXCEL_TO_ID_NORMALIZED:
        return _EXCEL_TO_ID_NORMALIZED[
            normalized_key
        ]

    # ------------------------------------------------------------------------
    # 5. Normalized alias fallback
    # ------------------------------------------------------------------------

    for alias, parameter_id in _ALIAS_TO_ID.items():

        alias_normalized = (
            alias
            .replace(" ", "_")
        )

        if alias_normalized == normalized_key:
            return parameter_id

    return None


# ============================================================================
# LIST PARAMETERS
# ============================================================================

def list_parameters() -> list[str]:
    """
    Return all canonical parameter IDs available
    in the maintenance knowledge base.
    """

    return [
        p["parameter_id"]
        for p in PARAMETERS
    ]


# ============================================================================
# LIST EXCEL MAPPINGS
# ============================================================================

def get_excel_parameter_mapping() -> dict[str, str]:
    """
    Return the Excel column -> canonical parameter mapping.
    """

    return EXCEL_TO_PARAMETER_ID.copy()


# ============================================================================
# PARAMETER BAND
# ============================================================================

def get_parameter_band(
    parameter_id: str,
) -> Optional[dict]:
    """
    Return threshold/band information for a parameter.
    """

    return _PARAM_BY_ID.get(
        parameter_id
    )


# ============================================================================
# SENSOR INFORMATION
# ============================================================================

def get_sensor(
    parameter_id: str,
) -> list[dict]:
    """
    Return all sensor information associated
    with a parameter.
    """

    return [
        sensor
        for sensor in SENSORS
        if sensor["parameter_id"] == parameter_id
    ]


# ============================================================================
# FAILURE MODES
# ============================================================================

def get_failure_modes(
    parameter_id: str,
) -> list[dict]:
    """
    Return all failure modes associated
    with a parameter.
    """

    return [
        failure_mode
        for failure_mode in FAILURE_MODES
        if parameter_id
        in failure_mode["parameters"]
    ]


# ============================================================================
# PROCEDURES
# ============================================================================

def get_procedures(
    parameter_id: str,
) -> list[dict]:
    """
    Return all procedures associated
    with a parameter.
    """

    return [
        procedure
        for procedure in PROCEDURES
        if parameter_id
        in procedure["parameters"]
    ]


# ============================================================================
# INSPECTION INTERVALS
# ============================================================================

def get_inspection_intervals(
    parameter_id: str,
) -> list[dict]:
    """
    Return inspection intervals associated
    with a parameter.

    This uses the INSPECTION_INTERVALS table if
    parameter_id is present in its records.
    """

    results = []

    for interval in INSPECTION_INTERVALS:

        # Handle parameter-based records

        if (
            "parameter_id" in interval
            and interval["parameter_id"]
            == parameter_id
        ):
            results.append(interval)
            continue

        # Handle parameter lists if present

        if (
            "parameters" in interval
            and parameter_id
            in interval["parameters"]
        ):
            results.append(interval)

    return results


# ============================================================================
# TROUBLESHOOTING TREE
# ============================================================================

def get_troubleshooting_tree(
    parameter_id: str,
) -> list[dict]:
    """
    Return troubleshooting information
    associated with a parameter.
    """

    return [
        tree
        for tree in TROUBLESHOOTING_TREES
        if tree["parameter_id"] == parameter_id
    ]


# ============================================================================
# DECISION MATRIX
# ============================================================================

def get_decision_tier(
    risk_score: float,
) -> Optional[dict]:
    """
    Return the decision-matrix tier corresponding
    to a risk score.
    """

    if risk_score is None:
        return None

    for tier in DECISION_MATRIX:

        if (
            tier["risk_min"]
            <= risk_score
            <= tier["risk_max"]
        ):
            return tier

    return None


# ============================================================================
# FAILURE MODE BY NAME
# ============================================================================

def get_failure_mode_by_name(
    name: str,
) -> Optional[dict]:
    """
    Retrieve a failure mode by exact name,
    case-insensitive.
    """

    if not name:
        return None

    name_lower = (
        name
        .strip()
        .lower()
    )

    for failure_mode in FAILURE_MODES:

        if (
            failure_mode["name"]
            .lower()
            == name_lower
        ):
            return failure_mode

    return None


# ============================================================================
# GLOSSARY LOOKUP
# ============================================================================

def get_glossary_term(
    term: str,
) -> Optional[dict]:
    """
    Retrieve a glossary definition.
    """

    if not term:
        return None

    term_lower = (
        term
        .strip()
        .lower()
    )

    for entry in GLOSSARY:

        # Support common key names.

        entry_term = (
            entry.get("term")
            or entry.get("name")
        )

        if (
            entry_term
            and entry_term.lower()
            == term_lower
        ):
            return entry

    return None


# ============================================================================
# MAIN PARAMETER RETRIEVER
# ============================================================================

def retrieve_parameter_context(
    parameter_id_or_alias: str,
) -> dict:
    """
    Retrieve EVERYTHING the maintenance manual says
    about a single parameter.

    Input can be:

        Canonical ID:
            oil_pressure

        Excel column:
            Oil_Pressure_(PSI)

        Alias:
            oil PSI

    Returns:

        {
            "parameter_id": ...,
            "thresholds": ...,
            "sensor": ...,
            "failure_modes": ...,
            "procedures": ...,
            "inspection_intervals": ...,
            "troubleshooting_tree": ...
        }
    """

    # ------------------------------------------------------------------------
    # Resolve parameter
    # ------------------------------------------------------------------------

    parameter_id = resolve_parameter_id(
        parameter_id_or_alias
    )

    # ------------------------------------------------------------------------
    # Unknown parameter
    # ------------------------------------------------------------------------

    if parameter_id is None:

        return {
            "error": (
                f"Unknown parameter: "
                f"'{parameter_id_or_alias}'"
            ),
            "known_parameters": list_parameters(),
            "excel_parameter_mapping": (
                get_excel_parameter_mapping()
            ),
        }

    # ------------------------------------------------------------------------
    # Retrieve all manual evidence
    # ------------------------------------------------------------------------

    return {

        "parameter_id": parameter_id,

        "thresholds": get_parameter_band(
            parameter_id
        ),

        "sensor": get_sensor(
            parameter_id
        ),

        "failure_modes": get_failure_modes(
            parameter_id
        ),

        "procedures": get_procedures(
            parameter_id
        ),

        "inspection_intervals": (
            get_inspection_intervals(
                parameter_id
            )
        ),

        "troubleshooting_tree": (
            get_troubleshooting_tree(
                parameter_id
            )
        ),
    }


# ============================================================================
# CLASSIFY VALUE USING MANUAL THRESHOLDS
# ============================================================================

def classify_value(
    parameter_id_or_alias: str,
    value: float,
) -> dict:
    """
    Classify a parameter reading against
    the maintenance-manual thresholds.

    This is deterministic threshold logic.

    It does NOT use:
        - LLM
        - embeddings
        - statistical analysis
        - historical data
    """

    # ------------------------------------------------------------------------
    # Resolve parameter
    # ------------------------------------------------------------------------

    parameter_id = resolve_parameter_id(
        parameter_id_or_alias
    )

    if parameter_id is None:

        return {
            "parameter_id": parameter_id_or_alias,
            "value": value,
            "status": "UNKNOWN",
            "manual_evidence_available": False,
            "reason": (
                f"Unknown parameter: "
                f"'{parameter_id_or_alias}'"
            ),
        }

    # ------------------------------------------------------------------------
    # Get threshold information
    # ------------------------------------------------------------------------

    band = get_parameter_band(
        parameter_id
    )

    if band is None:

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

    # ------------------------------------------------------------------------
    # Extract thresholds
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # Default
    # ------------------------------------------------------------------------

    status = "Normal"

    # ========================================================================
    # ABOVE DIRECTION
    # ========================================================================

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

    # ========================================================================
    # BELOW DIRECTION
    # ========================================================================

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

    # ========================================================================
    # OUTSIDE NORMAL BAND
    # ========================================================================

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

    # ========================================================================
    # FALLBACK
    # ========================================================================

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

    # ------------------------------------------------------------------------
    # Return classification
    # ------------------------------------------------------------------------

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
            [
                normal_min,
                normal_max,
            ]
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