
# -*- coding: utf-8 -*-

"""
Aircraft Maintenance Analytics

Responsibilities
----------------
    - Load aircraft flight history when no DataFrame is provided
    - Identify latest flight
    - Calculate historical statistics
    - Compare latest value against historical baseline
    - Calculate recent trend
    - Detect anomalies using maintenance-manual normal ranges

This module does NOT:
    - Retrieve PDF/manual information
    - Call the LLM
    - Perform maintenance reasoning
    - Call LangGraph
    - Call FastAPI

IMPORTANT
---------
Anomaly detection is based on the predefined normal range
for each parameter.

Z-score is calculated only as supporting statistical information.
It does NOT determine anomaly status.

The pipeline supports a user-uploaded Excel DataFrame.
"""

import numpy as np
import pandas as pd

from src.config import TREND_WINDOW
from src.data_loader import load_dataset

from src.schemas import (
    ParameterAnalytics,
    HistoricalAnalytics,
)


# ============================================================================
# PARAMETERS TO MONITOR
# ============================================================================

MONITORING_PARAMETERS = [
    "Ambient_Temperature_(°C)",
    "Humidity_(%)",
    "Outside_Air_Temperature_(°C)",
    "Engine_Temperature_(°C)",
    "Exhaust_Gas_Temperature_(°C)",
    "Oil_Temperature_(°C)",
    "Oil_Pressure_(PSI)",
    "Engine_Vibration_(mm/s)",
    "Compressor_Pressure_(PSI)",
    "Fuel_Flow_(kg/hr)",
    "Hydraulic_Pressure_(PSI)",
    "Engine_RPM",
    "Risk_Score_(%)",
    "Remaining_Useful_Life_(cycles)",
]


# ============================================================================
# MAINTENANCE-MANUAL NORMAL RANGES
# ============================================================================

PARAMETER_NORMAL_RANGES = {

    "Ambient_Temperature_(°C)": {
        "min": -10.0,
        "max": 35.0,
    },

    "Humidity_(%)": {
        "min": 20.0,
        "max": 88.0,
    },

    "Outside_Air_Temperature_(°C)": {
        "min": -19.0,
        "max": 28.0,
    },

    "Engine_Temperature_(°C)": {
        "min": 640.0,
        "max": 676.0,
    },

    "Exhaust_Gas_Temperature_(°C)": {
        "min": 615.0,
        "max": 648.0,
    },

    "Oil_Temperature_(°C)": {
        "min": 82.0,
        "max": 92.0,
    },

    "Oil_Pressure_(PSI)": {
        "min": 55.0,
        "max": 61.0,
    },

    "Engine_Vibration_(mm/s)": {
        "min": 0.0,
        "max": 3.1,
    },

    "Compressor_Pressure_(PSI)": {
        "min": 38.5,
        "max": 41.5,
    },

    "Fuel_Flow_(kg/hr)": {
        "min": 2235.0,
        "max": 2338.0,
    },

    "Hydraulic_Pressure_(PSI)": {
        "min": 2950.0,
        "max": 3050.0,
    },

    "Engine_RPM": {
        "min": 9700.0,
        "max": 9900.0,
    },

    # No maintenance-manual normal range
    "Risk_Score_(%)": None,

    # No maintenance-manual normal range
    "Remaining_Useful_Life_(cycles)": None,
}


# ============================================================================
# FLIGHT CYCLE COLUMN
# ============================================================================
#
# IMPORTANT:
#
# app.py normalizes:
#
#     Flight_Cycle (cycles)
#
# into:
#
#     Flight_Cycle_(cycles)
#
# Therefore analytics.py must use the normalized column name.
#
# ============================================================================

FLIGHT_CYCLE_COLUMN = "Flight_Cycle_(cycles)"


# ============================================================================
# NORMAL RANGE LOOKUP
# ============================================================================

def get_normal_range(
    parameter: str,
) -> tuple[float | None, float | None]:
    """
    Return the maintenance-manual normal range
    for a parameter.

    Returns
    -------
    tuple
        (minimum, maximum)

    If no manual normal range exists:
        (None, None)
    """

    range_info = PARAMETER_NORMAL_RANGES.get(
        parameter
    )

    if not range_info:
        return None, None

    return (
        range_info["min"],
        range_info["max"],
    )


# ============================================================================
# HISTORICAL BASELINE
# ============================================================================

def calculate_baseline(
    history: pd.DataFrame,
    parameter: str,
) -> HistoricalAnalytics:
    """
    Calculate historical statistics for one parameter.
    """

    if parameter not in history.columns:
        return HistoricalAnalytics(
            count=0,
            mean=None,
            median=None,
            std=None,
            minimum=None,
            maximum=None,
        )

    values = (
        pd.to_numeric(
            history[parameter],
            errors="coerce",
        )
        .dropna()
    )

    if len(values) == 0:
        return HistoricalAnalytics(
            count=0,
            mean=None,
            median=None,
            std=None,
            minimum=None,
            maximum=None,
        )

    if len(values) > 1:
        std = float(
            values.std(
                ddof=1
            )
        )
    else:
        std = 0.0

    return HistoricalAnalytics(
        count=int(len(values)),
        mean=float(values.mean()),
        median=float(values.median()),
        std=std,
        minimum=float(values.min()),
        maximum=float(values.max()),
    )


# ============================================================================
# RANGE-BASED ANOMALY DETECTION
# ============================================================================

def detect_range_anomaly(
    parameter: str,
    value: float,
) -> tuple[bool, str]:
    """
    Determine anomaly using the maintenance-manual
    normal range.

    Z-score is NOT used here.

    Returns
    -------
    tuple
        anomaly, status
    """

    normal_min, normal_max = get_normal_range(
        parameter
    )

    # ------------------------------------------------------------------------
    # No manual range available
    # ------------------------------------------------------------------------

    if (
        normal_min is None
        or normal_max is None
    ):
        return False, "NO_RANGE"

    # ------------------------------------------------------------------------
    # Outside normal range
    # ------------------------------------------------------------------------

    if (
        value < normal_min
        or value > normal_max
    ):
        return True, "ANOMALY"

    # ------------------------------------------------------------------------
    # Inside normal range
    # ------------------------------------------------------------------------

    return False, "NORMAL"


# ============================================================================
# LATEST VS HISTORICAL BASELINE
# ============================================================================

def compare_parameter(
    latest_value,
    history: pd.DataFrame,
    parameter: str,
) -> ParameterAnalytics:
    """
    Compare latest parameter value against:

        1. Historical baseline
        2. Maintenance-manual normal range

    Anomaly detection is based ONLY on the
    maintenance-manual normal range.

    Z-score is calculated for reference only.
    """

    baseline = calculate_baseline(
        history=history,
        parameter=parameter,
    )

    # ------------------------------------------------------------------------
    # Missing latest value
    # ------------------------------------------------------------------------

    if pd.isna(latest_value):

        return ParameterAnalytics(
            latest_value=None,
            historical=baseline,
            difference_from_mean=None,
            percentage_change=None,
            z_score=None,
            trend_slope=None,
            trend="INSUFFICIENT_DATA",
            statistical_anomaly=False,
            statistical_status="NO_DATA",
        )

    latest_value = float(
        latest_value
    )

    mean = baseline.mean
    std = baseline.std

    # ========================================================================
    # DIFFERENCE FROM MEAN
    # ========================================================================

    difference = None

    if mean is not None:
        difference = float(
            latest_value - mean
        )

    # ========================================================================
    # PERCENTAGE CHANGE
    # ========================================================================

    percentage_change = None

    if (
        mean is not None
        and mean != 0
    ):
        percentage_change = float(
            (
                (latest_value - mean)
                / abs(mean)
            ) * 100
        )

    # ========================================================================
    # Z-SCORE
    # ========================================================================

    z_score = None

    if (
        mean is not None
        and std is not None
        and std > 0
    ):
        z_score = float(
            (latest_value - mean)
            / std
        )

    elif (
        std is not None
        and std == 0
    ):
        z_score = 0.0

    # ========================================================================
    # RANGE-BASED ANOMALY
    # ========================================================================

    anomaly, status = detect_range_anomaly(
        parameter=parameter,
        value=latest_value,
    )

    # ========================================================================
    # TREND
    # ========================================================================

    trend_slope, trend = calculate_trend(
        history=history,
        parameter=parameter,
        window=TREND_WINDOW,
    )

    # ========================================================================
    # RETURN
    # ========================================================================

    return ParameterAnalytics(
        latest_value=latest_value,
        historical=baseline,
        difference_from_mean=difference,
        percentage_change=percentage_change,
        z_score=z_score,
        trend_slope=trend_slope,
        trend=trend,
        statistical_anomaly=anomaly,
        statistical_status=status,
    )


# ============================================================================
# TREND ANALYSIS
# ============================================================================

def calculate_trend(
    history: pd.DataFrame,
    parameter: str,
    window: int = TREND_WINDOW,
) -> tuple[float | None, str]:
    """
    Calculate trend using linear regression
    over the most recent historical values.
    """

    if parameter not in history.columns:
        return None, "INSUFFICIENT_DATA"

    values = (
        pd.to_numeric(
            history[parameter],
            errors="coerce",
        )
        .dropna()
        .tail(window)
    )

    if len(values) < 2:
        return None, "INSUFFICIENT_DATA"

    x = np.arange(
        len(values)
    )

    slope = float(
        np.polyfit(
            x,
            values.values,
            1,
        )[0]
    )

    if slope > 0:
        trend = "INCREASING"

    elif slope < 0:
        trend = "DECREASING"

    else:
        trend = "STABLE"

    return slope, trend


# ============================================================================
# ANALYZE ONE PARAMETER
# ============================================================================

def analyze_parameter(
    latest: pd.Series,
    history: pd.DataFrame,
    parameter: str,
) -> ParameterAnalytics:
    """
    Analyze one parameter for the latest flight.
    """

    latest_value = latest.get(
        parameter,
        np.nan,
    )

    return compare_parameter(
        latest_value=latest_value,
        history=history,
        parameter=parameter,
    )


# ============================================================================
# ANALYZE ONE AIRCRAFT
# ============================================================================

def analyze_aircraft(
    aircraft_df: pd.DataFrame,
) -> dict[str, ParameterAnalytics]:
    """
    Analyze latest flight of one aircraft
    against all previous flights.
    """

    if aircraft_df.empty:
        return {}

    # ========================================================================
    # VALIDATE FLIGHT CYCLE COLUMN
    # ========================================================================

    if FLIGHT_CYCLE_COLUMN not in aircraft_df.columns:

        raise ValueError(
            f"Required column '{FLIGHT_CYCLE_COLUMN}' "
            "not found in dataset."
        )

    # ========================================================================
    # CONVERT FLIGHT CYCLE TO NUMERIC
    # ========================================================================

    aircraft_df = aircraft_df.copy()

    aircraft_df[FLIGHT_CYCLE_COLUMN] = (
        pd.to_numeric(
            aircraft_df[
                FLIGHT_CYCLE_COLUMN
            ],
            errors="coerce",
        )
    )

    # ========================================================================
    # REMOVE ROWS WITHOUT FLIGHT CYCLE
    # ========================================================================

    aircraft_df = aircraft_df.dropna(
        subset=[
            FLIGHT_CYCLE_COLUMN
        ]
    )

    if aircraft_df.empty:

        raise ValueError(
            "No valid Flight_Cycle_(cycles) values "
            "found for this aircraft."
        )

    # ========================================================================
    # SORT BY FLIGHT CYCLE
    # ========================================================================

    aircraft_df = (
        aircraft_df
        .sort_values(
            FLIGHT_CYCLE_COLUMN
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================================
    # NEED HISTORICAL + LATEST
    # ========================================================================

    if len(aircraft_df) < 2:
        return {}

    latest = aircraft_df.iloc[-1]

    history = aircraft_df.iloc[:-1]

    results = {}

    # ========================================================================
    # ANALYZE EVERY PARAMETER
    # ========================================================================

    for parameter in MONITORING_PARAMETERS:

        if parameter not in aircraft_df.columns:
            continue

        results[parameter] = analyze_parameter(
            latest=latest,
            history=history,
            parameter=parameter,
        )

    return results


# ============================================================================
# ANALYZE AIRCRAFT BY ID
# ============================================================================

def run_aircraft_analytics(
    aircraft_id: str,
    df: pd.DataFrame | None = None,
) -> dict[str, ParameterAnalytics]:
    """
    Run analytics for a specific aircraft.

    If df is supplied, the uploaded DataFrame is used.

    If df is None, the configured local dataset
    is loaded as a fallback.
    """

    # ========================================================================
    # LOAD DATA ONLY WHEN NO DATAFRAME WAS PROVIDED
    # ========================================================================

    if df is None:
        df = load_dataset()

    # ========================================================================
    # VALIDATE DATAFRAME
    # ========================================================================

    if not isinstance(
        df,
        pd.DataFrame,
    ):
        raise TypeError(
            "df must be a pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Dataset is empty."
        )

    # ========================================================================
    # AIRCRAFT ID COLUMN
    # ========================================================================

    if "Aircraft_ID" not in df.columns:

        raise ValueError(
            "Aircraft_ID column not found."
        )

    # ========================================================================
    # NORMALIZE AIRCRAFT IDs
    # ========================================================================

    df = df.copy()

    df["Aircraft_ID"] = (
        df["Aircraft_ID"]
        .astype(str)
        .str.strip()
    )

    aircraft_id = str(
        aircraft_id
    ).strip()

    # ========================================================================
    # FILTER AIRCRAFT
    # ========================================================================

    aircraft_df = df[
        df["Aircraft_ID"] == aircraft_id
    ].copy()

    if aircraft_df.empty:

        raise ValueError(
            f"Aircraft '{aircraft_id}' not found."
        )

    # ========================================================================
    # RUN ANALYTICS
    # ========================================================================

    return analyze_aircraft(
        aircraft_df
    )


# ============================================================================
# ANALYZE ALL AIRCRAFT
# ============================================================================

def run_all_analytics(
    df: pd.DataFrame | None = None,
) -> dict[str, dict[str, ParameterAnalytics]]:
    """
    Run analytics for every aircraft.

    If df is supplied, the uploaded DataFrame is used.
    """

    # ========================================================================
    # LOAD DATA ONLY WHEN NO DATAFRAME WAS PROVIDED
    # ========================================================================

    if df is None:
        df = load_dataset()

    # ========================================================================
    # VALIDATE
    # ========================================================================

    if not isinstance(
        df,
        pd.DataFrame,
    ):
        raise TypeError(
            "df must be a pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Dataset is empty."
        )

    if "Aircraft_ID" not in df.columns:

        raise ValueError(
            "Aircraft_ID column not found."
        )

    # ========================================================================
    # NORMALIZE IDs
    # ========================================================================

    df = df.copy()

    df["Aircraft_ID"] = (
        df["Aircraft_ID"]
        .astype(str)
        .str.strip()
    )

    # ========================================================================
    # ANALYZE EVERY AIRCRAFT
    # ========================================================================

    all_results = {}

    for aircraft_id, aircraft_df in df.groupby(
        "Aircraft_ID"
    ):

        all_results[aircraft_id] = (
            analyze_aircraft(
                aircraft_df
            )
        )

    return all_results


# ============================================================================
# BACKWARD-COMPATIBLE ALIAS
# ============================================================================

def run_analytics(
    aircraft_id: str,
    df: pd.DataFrame | None = None,
):
    """
    Backward-compatible wrapper.

    Existing code can call:

        run_analytics("AIR-001")

    or:

        run_analytics(
            "AIR-001",
            df=uploaded_dataframe
        )
    """

    return run_aircraft_analytics(
        aircraft_id=aircraft_id,
        df=df,
    )
