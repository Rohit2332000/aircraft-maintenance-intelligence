
# -*- coding: utf-8 -*-

"""
TEST: Aircraft Maintenance Analytics

This test checks ONLY src/analytics.py.

It does NOT:
    - call the LLM
    - retrieve the maintenance manual
    - run LangGraph
    - perform maintenance reasoning

It verifies:
    1. Dataset loads correctly
    2. Aircraft exists
    3. Latest flight cycle is identified
    4. All monitoring parameters are analyzed
    5. Latest values are present
    6. Historical statistics are present
    7. Z-score is calculated
    8. Statistical anomaly detection works
    9. Normal and anomalous parameters are separated
"""

import json
import sys
from pathlib import Path


# ============================================================================
# PROJECT PATH
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================================
# IMPORTS
# ============================================================================

from src.analytics import (
    run_aircraft_analytics,
    MONITORING_PARAMETERS,
)

from src.data_loader import load_dataset


# ============================================================================
# CONFIG
# ============================================================================

AIRCRAFT_ID = "AIR-001"


# ============================================================================
# HELPERS
# ============================================================================

def model_to_dict(value):
    """
    Convert Pydantic model to dictionary.
    """
    if value is None:
        return {}

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    if isinstance(value, dict):
        return value

    return {}


# ============================================================================
# HEADER
# ============================================================================

print()
print("=" * 100)
print("AIRCRAFT MAINTENANCE ANALYTICS TEST")
print("=" * 100)


# ============================================================================
# 1. LOAD DATASET
# ============================================================================

print()
print("Loading dataset...")

try:
    df = load_dataset()

    print("✓ Dataset loaded successfully")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {len(df.columns)}")

except Exception as exc:
    print()
    print("✗ DATASET LOAD FAILED")
    print(f"  Error: {exc}")
    raise


# ============================================================================
# 2. CHECK AIRCRAFT
# ============================================================================

print()
print("=" * 100)
print("AIRCRAFT CHECK")
print("=" * 100)

if "Aircraft_ID" not in df.columns:
    raise ValueError(
        "Aircraft_ID column not found in dataset."
    )

aircraft_df = df[
    df["Aircraft_ID"] == AIRCRAFT_ID
].copy()

if aircraft_df.empty:
    raise ValueError(
        f"Aircraft '{AIRCRAFT_ID}' not found."
    )

print(f"✓ Aircraft found: {AIRCRAFT_ID}")
print(f"  Records: {len(aircraft_df)}")


# ============================================================================
# 3. LATEST FLIGHT
# ============================================================================

print()
print("=" * 100)
print("LATEST FLIGHT")
print("=" * 100)

if "Flight_Cycle_(cycles)" in aircraft_df.columns:

    aircraft_df = (
        aircraft_df
        .sort_values("Flight_Cycle_(cycles)")
        .reset_index(drop=True)
    )

    latest = aircraft_df.iloc[-1]

    latest_cycle = latest[
        "Flight_Cycle_(cycles)"
    ]

    print(
        f"✓ Latest flight cycle: {latest_cycle}"
    )

else:
    print(
        "WARNING: Flight_Cycle_(cycles) column not found."
    )


# ============================================================================
# 4. RUN ANALYTICS
# ============================================================================

print()
print("=" * 100)
print("RUNNING AIRCRAFT ANALYTICS")
print("=" * 100)

try:

    analytics_result = run_aircraft_analytics(
        aircraft_id=AIRCRAFT_ID,
        df=df,
    )

except Exception as exc:

    print()
    print("✗ ANALYTICS FAILED")
    print(f"  Error: {exc}")
    raise


print()
print(
    f"✓ Analytics returned "
    f"{len(analytics_result)} parameters."
)


# ============================================================================
# 5. PARAMETER COVERAGE
# ============================================================================

print()
print("=" * 100)
print("PARAMETER COVERAGE")
print("=" * 100)

returned_parameters = list(
    analytics_result.keys()
)

missing_parameters = []

for parameter in MONITORING_PARAMETERS:

    if parameter in analytics_result:
        print(f"✓ {parameter}")
    else:
        print(f"✗ MISSING: {parameter}")
        missing_parameters.append(parameter)


print()
print(
    f"Expected parameters: {len(MONITORING_PARAMETERS)}"
)

print(
    f"Returned parameters: {len(returned_parameters)}"
)

print(
    f"Missing parameters: {len(missing_parameters)}"
)


# ============================================================================
# 6. DETAILED ANALYTICS
# ============================================================================

print()
print("=" * 100)
print("DETAILED ANALYTICS RESULTS")
print("=" * 100)


anomalous_parameters = []
normal_parameters = []
no_data_parameters = []


for parameter, result in analytics_result.items():

    data = model_to_dict(result)

    historical = model_to_dict(
        data.get("historical")
    )

    latest_value = data.get(
        "latest_value"
    )

    mean = historical.get(
        "mean"
    )

    median = historical.get(
        "median"
    )

    std = historical.get(
        "std"
    )

    minimum = historical.get(
        "minimum"
    )

    maximum = historical.get(
        "maximum"
    )

    z_score = data.get(
        "z_score"
    )

    trend = data.get(
        "trend"
    )

    trend_slope = data.get(
        "trend_slope"
    )

    anomaly = data.get(
        "statistical_anomaly",
        False,
    )

    status = data.get(
        "statistical_status"
    )


    print()
    print("-" * 100)
    print(parameter)
    print("-" * 100)

    print(
        f"  Latest value       : {latest_value}"
    )

    print(
        f"  Historical count   : "
        f"{historical.get('count')}"
    )

    print(
        f"  Historical mean    : {mean}"
    )

    print(
        f"  Historical median  : {median}"
    )

    print(
        f"  Historical std     : {std}"
    )

    print(
        f"  Historical minimum : {minimum}"
    )

    print(
        f"  Historical maximum : {maximum}"
    )

    print(
        f"  Difference from mean: "
        f"{data.get('difference_from_mean')}"
    )

    print(
        f"  Percentage change  : "
        f"{data.get('percentage_change')}"
    )

    print(
        f"  Z-score            : {z_score}"
    )

    print(
        f"  Trend slope        : {trend_slope}"
    )

    print(
        f"  Trend              : {trend}"
    )

    print(
        f"  Statistical anomaly: {anomaly}"
    )

    print(
        f"  Statistical status : {status}"
    )


    # ------------------------------------------------------------
    # CLASSIFY
    # ------------------------------------------------------------

    if status == "NO_DATA":
        no_data_parameters.append(
            parameter
        )

    elif anomaly:
        anomalous_parameters.append(
            parameter
        )

    else:
        normal_parameters.append(
            parameter
        )


# ============================================================================
# 7. NORMAL PARAMETERS
# ============================================================================

print()
print("=" * 100)
print("NORMAL PARAMETERS")
print("=" * 100)

if normal_parameters:

    for parameter in normal_parameters:

        data = model_to_dict(
            analytics_result[parameter]
        )

        print(
            f"✓ {parameter}"
        )

        print(
            f"    Value : "
            f"{data.get('latest_value')}"
        )

        print(
            f"    Z-score : "
            f"{data.get('z_score')}"
        )

        print(
            f"    Status : "
            f"{data.get('statistical_status')}"
        )

else:

    print(
        "No normal parameters detected."
    )


# ============================================================================
# 8. ANOMALOUS PARAMETERS
# ============================================================================

print()
print("=" * 100)
print("ANOMALOUS PARAMETERS")
print("=" * 100)

if anomalous_parameters:

    for parameter in anomalous_parameters:

        data = model_to_dict(
            analytics_result[parameter]
        )

        print(
            f"⚠ {parameter}"
        )

        print(
            f"    Value : "
            f"{data.get('latest_value')}"
        )

        print(
            f"    Mean : "
            f"{model_to_dict(data.get('historical')).get('mean')}"
        )

        print(
            f"    Z-score : "
            f"{data.get('z_score')}"
        )

        print(
            f"    Status : "
            f"{data.get('statistical_status')}"
        )

        print(
            f"    Trend : "
            f"{data.get('trend')}"
        )

else:

    print(
        "No statistical anomalies detected."
    )


# ============================================================================
# 9. NO DATA PARAMETERS
# ============================================================================

print()
print("=" * 100)
print("NO-DATA PARAMETERS")
print("=" * 100)

if no_data_parameters:

    for parameter in no_data_parameters:
        print(
            f"⚠ {parameter}"
        )

else:

    print(
        "✓ No parameters have insufficient data."
    )


# ============================================================================
# 10. VALIDATION
# ============================================================================

print()
print("=" * 100)
print("ANALYTICS VALIDATION")
print("=" * 100)

validation_passed = True


# ------------------------------------------------------------
# Parameter count
# ------------------------------------------------------------

if len(analytics_result) != len(
    [
        p
        for p in MONITORING_PARAMETERS
        if p in df.columns
    ]
):

    print(
        "✗ Parameter count mismatch."
    )

    validation_passed = False

else:

    print(
        "✓ Parameter count is correct."
    )


# ------------------------------------------------------------
# Check values
# ------------------------------------------------------------

for parameter, result in analytics_result.items():

    data = model_to_dict(result)

    if data.get("latest_value") is None:

        print(
            f"✗ {parameter}: latest_value is None"
        )

        validation_passed = False

    else:

        print(
            f"✓ {parameter}: latest value present"
        )


# ------------------------------------------------------------
# Check anomaly consistency
# ------------------------------------------------------------

for parameter, result in analytics_result.items():

    data = model_to_dict(result)

    z_score = data.get(
        "z_score"
    )

    anomaly = data.get(
        "statistical_anomaly"
    )

    status = data.get(
        "statistical_status"
    )


    if z_score is not None:

        # Read threshold from config
        from src.config import Z_SCORE_THRESHOLD

        expected_anomaly = (
            abs(z_score)
            >= Z_SCORE_THRESHOLD
        )

        if anomaly != expected_anomaly:

            print(
                f"✗ {parameter}: "
                f"anomaly flag inconsistent "
                f"with z-score."
            )

            validation_passed = False

        else:

            print(
                f"✓ {parameter}: "
                f"anomaly flag consistent"
            )


# ============================================================================
# 11. FINAL SUMMARY
# ============================================================================

print()
print("=" * 100)
print("FINAL ANALYTICS TEST SUMMARY")
print("=" * 100)

print(
    f"Aircraft              : {AIRCRAFT_ID}"
)

print(
    f"Dataset records       : {len(aircraft_df)}"
)

print(
    f"Parameters monitored  : "
    f"{len(MONITORING_PARAMETERS)}"
)

print(
    f"Parameters returned   : "
    f"{len(analytics_result)}"
)

print(
    f"Normal parameters     : "
    f"{len(normal_parameters)}"
)

print(
    f"Anomalous parameters  : "
    f"{len(anomalous_parameters)}"
)

print(
    f"No-data parameters    : "
    f"{len(no_data_parameters)}"
)


# ============================================================================
# FINAL RESULT
# ============================================================================

print()
print("=" * 100)

if validation_passed:

    print(
        "✓ ANALYTICS TEST PASSED"
    )

else:

    print(
        "✗ ANALYTICS TEST FAILED"
    )

print("=" * 100)
