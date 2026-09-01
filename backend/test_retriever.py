# -*- coding: utf-8 -*-

"""
Retriever.py Test

Tests the exact functionality implemented in src/retriever.py:

1. Parameter resolution
2. Excel column -> parameter ID mapping
3. Parameter list
4. Parameter band / thresholds
5. Sensor information
6. Failure modes
7. Procedures
8. Inspection intervals
9. Troubleshooting tree
10. Decision matrix
11. Failure mode lookup
12. Glossary lookup
13. Complete parameter context
14. Deterministic value classification

NO LLM
NO analytics
NO LangGraph
NO Excel loading
"""

from pprint import pprint

from src.retriever import (
    resolve_parameter_id,
    list_parameters,
    get_excel_parameter_mapping,
    get_parameter_band,
    get_sensor,
    get_failure_modes,
    get_procedures,
    get_inspection_intervals,
    get_troubleshooting_tree,
    get_decision_tier,
    get_failure_mode_by_name,
    get_glossary_term,
    retrieve_parameter_context,
    classify_value,
)


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

PARAMETER = "Oil_Pressure_(PSI)"
VALUE = 100.0


# ============================================================================
# HEADER
# ============================================================================

print("\n")
print("=" * 100)
print("                 RETRIEVER.PY TEST")
print("=" * 100)


# ============================================================================
# 1. RESOLVE PARAMETER
# ============================================================================

print("\n" + "=" * 100)
print("1. PARAMETER RESOLUTION")
print("=" * 100)

parameter_id = resolve_parameter_id(PARAMETER)

print(f"Input          : {PARAMETER}")
print(f"Parameter ID   : {parameter_id}")

if parameter_id:
    print("STATUS         : PASS")
else:
    print("STATUS         : FAIL")


# ============================================================================
# 2. TEST ALIAS / DIFFERENT INPUT FORMATS
# ============================================================================

print("\n" + "=" * 100)
print("2. PARAMETER RESOLUTION VARIANTS")
print("=" * 100)

test_inputs = [
    "oil_pressure",
    "oil pressure",
    "Oil_Pressure_(PSI)",
    "oil PSI",
]

for test_input in test_inputs:

    result = resolve_parameter_id(test_input)

    print(
        f"{test_input:<30} -> {result}"
    )


# ============================================================================
# 3. LIST PARAMETERS
# ============================================================================

print("\n" + "=" * 100)
print("3. AVAILABLE PARAMETERS")
print("=" * 100)

parameters = list_parameters()

print(f"Total parameters: {len(parameters)}")

for parameter in parameters:
    print(f" - {parameter}")


# ============================================================================
# 4. EXCEL PARAMETER MAPPING
# ============================================================================

print("\n" + "=" * 100)
print("4. EXCEL PARAMETER MAPPING")
print("=" * 100)

mapping = get_excel_parameter_mapping()

for excel_name, parameter_id in mapping.items():

    print(
        f"{excel_name:<45} -> {parameter_id}"
    )


# ============================================================================
# 5. PARAMETER BAND / THRESHOLDS
# ============================================================================

print("\n" + "=" * 100)
print("5. PARAMETER BAND / THRESHOLDS")
print("=" * 100)

band = get_parameter_band(parameter_id)

if band:

    pprint(band)

else:

    print("No parameter band found.")


# ============================================================================
# 6. NORMAL RANGE
# ============================================================================

print("\n" + "=" * 100)
print("6. NORMAL RANGE")
print("=" * 100)

if band:

    normal_min = band.get("normal_min")
    normal_max = band.get("normal_max")
    unit = band.get("unit", "")

    print(f"Parameter : {band.get('display_name')}")
    print(f"Unit      : {unit}")

    if (
        normal_min is not None
        and normal_max is not None
    ):

        print(
            f"Normal Range : "
            f"{normal_min} - {normal_max} {unit}"
        )

    else:

        print(
            "Normal Range : Not available"
        )

else:

    print(
        "Normal Range : No threshold data"
    )


# ============================================================================
# 7. SENSOR INFORMATION
# ============================================================================

print("\n" + "=" * 100)
print("7. SENSOR INFORMATION")
print("=" * 100)

sensors = get_sensor(parameter_id)

print(f"Number of sensor records: {len(sensors)}")

if sensors:
    pprint(sensors)
else:
    print("No sensor information found.")


# ============================================================================
# 8. FAILURE MODES
# ============================================================================

print("\n" + "=" * 100)
print("8. FAILURE MODES")
print("=" * 100)

failure_modes = get_failure_modes(parameter_id)

print(
    f"Number of failure modes: "
    f"{len(failure_modes)}"
)

if failure_modes:

    for i, failure in enumerate(
        failure_modes,
        start=1
    ):

        print(f"\nFailure Mode {i}")
        pprint(failure)

else:

    print(
        "No failure modes found."
    )


# ============================================================================
# 9. PROCEDURES
# ============================================================================

print("\n" + "=" * 100)
print("9. MAINTENANCE PROCEDURES")
print("=" * 100)

procedures = get_procedures(parameter_id)

print(
    f"Number of procedures: "
    f"{len(procedures)}"
)

if procedures:

    for i, procedure in enumerate(
        procedures,
        start=1
    ):

        print(f"\nProcedure {i}")
        pprint(procedure)

else:

    print(
        "No procedures found."
    )


# ============================================================================
# 10. INSPECTION INTERVALS
# ============================================================================

print("\n" + "=" * 100)
print("10. INSPECTION INTERVALS")
print("=" * 100)

inspection_intervals = (
    get_inspection_intervals(
        parameter_id
    )
)

print(
    f"Number of inspection intervals: "
    f"{len(inspection_intervals)}"
)

if inspection_intervals:

    for interval in inspection_intervals:

        pprint(interval)

else:

    print(
        "No inspection intervals found."
    )


# ============================================================================
# 11. TROUBLESHOOTING TREE
# ============================================================================

print("\n" + "=" * 100)
print("11. TROUBLESHOOTING TREE")
print("=" * 100)

troubleshooting = (
    get_troubleshooting_tree(
        parameter_id
    )
)

print(
    f"Number of troubleshooting records: "
    f"{len(troubleshooting)}"
)

if troubleshooting:

    for tree in troubleshooting:

        pprint(tree)

else:

    print(
        "No troubleshooting tree found."
    )


# ============================================================================
# 12. DECISION MATRIX
# ============================================================================

print("\n" + "=" * 100)
print("12. DECISION MATRIX")
print("=" * 100)

test_risk_score = 80.0

decision = get_decision_tier(
    test_risk_score
)

print(
    f"Risk Score : {test_risk_score}"
)

if decision:

    pprint(decision)

else:

    print(
        "No decision tier found."
    )


# ============================================================================
# 13. COMPLETE PARAMETER CONTEXT
# ============================================================================

print("\n" + "=" * 100)
print("13. COMPLETE PARAMETER CONTEXT")
print("=" * 100)

context = retrieve_parameter_context(
    PARAMETER
)

pprint(context)


# ============================================================================
# 14. CLASSIFY CURRENT VALUE
# ============================================================================

print("\n" + "=" * 100)
print("14. CLASSIFY CURRENT VALUE")
print("=" * 100)

classification = classify_value(
    PARAMETER,
    VALUE
)

pprint(classification)


# ============================================================================
# 15. HUMAN-READABLE CLASSIFICATION
# ============================================================================

print("\n" + "=" * 100)
print("15. CLASSIFICATION SUMMARY")
print("=" * 100)

print(
    f"Parameter       : "
    f"{classification.get('display_name')}"
)

print(
    f"Parameter ID    : "
    f"{classification.get('parameter_id')}"
)

print(
    f"Current Value   : "
    f"{classification.get('value')} "
    f"{classification.get('unit', '')}"
)

print(
    f"Normal Range    : "
    f"{classification.get('normal_range')}"
)

print(
    f"Manual Status   : "
    f"{classification.get('status')}"
)

print(
    f"Recommended     : "
    f"{classification.get('recommended_action')}"
)

print(
    f"Evidence        : "
    f"{classification.get('manual_evidence_available')}"
)


# ============================================================================
# 16. FAILURE MODE BY NAME
# ============================================================================

print("\n" + "=" * 100)
print("16. FAILURE MODE LOOKUP")
print("=" * 100)

if failure_modes:

    first_failure_name = failure_modes[0].get(
        "name"
    )

    print(
        f"Searching for: {first_failure_name}"
    )

    failure_lookup = (
        get_failure_mode_by_name(
            first_failure_name
        )
    )

    if failure_lookup:

        print("STATUS: PASS")
        pprint(failure_lookup)

    else:

        print("STATUS: FAIL")

else:

    print(
        "Skipped because no failure mode "
        "was returned."
    )


# ============================================================================
# 17. UNKNOWN PARAMETER TEST
# ============================================================================

print("\n" + "=" * 100)
print("17. UNKNOWN PARAMETER TEST")
print("=" * 100)

unknown_result = retrieve_parameter_context(
    "this_parameter_does_not_exist"
)

pprint(unknown_result)

if "error" in unknown_result:

    print("STATUS: PASS")

else:

    print(
        "STATUS: FAIL"
    )


# ============================================================================
# FINAL
# ============================================================================

print("\n" + "=" * 100)
print("                 RETRIEVER TEST COMPLETED")
print("=" * 100)