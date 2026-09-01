
# -*- coding: utf-8 -*-

"""
Aircraft Maintenance Intelligence Pipeline

Responsibilities
----------------
This module is the main orchestration layer between the
LangGraph workflow and the FastAPI application.

Flow
----
FastAPI
   |
   v
Uploaded Excel
   |
   v
pipeline.py
   |
   v
graph.py
   |
   +--> analytics.py
   |
   +--> retriever.py
   |
   +--> llm.py
   |
   v
Final Maintenance Result

IMPORTANT
---------
1. pipeline.py does NOT contain business logic.
2. pipeline.py does NOT call the LLM directly.
3. pipeline.py does NOT perform retrieval directly.
4. graph.py controls the maintenance workflow.
5. analytics.py determines statistical/manual conditions.
6. Only required/anomalous parameters reach the LLM.
7. This module is designed to be imported by FastAPI.
8. FastAPI can provide an uploaded DataFrame.
9. file_path is NOT required.
10. The default Excel loader is retained for testing/notebooks.
"""

from typing import Any

import pandas as pd

from src.graph import run_maintenance_analysis
from src.data_loader import load_dataset


# ============================================================================
# PIPELINE VERSION
# ============================================================================

PIPELINE_VERSION = "1.1.0"


# ============================================================================
# VALIDATE AIRCRAFT ID
# ============================================================================

def _validate_aircraft_id(
    aircraft_id: str,
) -> str:
    """
    Validate aircraft identifier before running the pipeline.
    """

    if aircraft_id is None:
        raise ValueError(
            "aircraft_id is required."
        )

    aircraft_id = str(
        aircraft_id
    ).strip()

    if not aircraft_id:
        raise ValueError(
            "aircraft_id cannot be empty."
        )

    return aircraft_id


# ============================================================================
# VALIDATE DATAFRAME
# ============================================================================

def _validate_dataframe(
    df: pd.DataFrame,
) -> None:
    """
    Validate the dataframe required by the pipeline.
    """

    if df is None:
        raise ValueError(
            "Dataset cannot be None."
        )

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
            "Aircraft_ID column not found in dataset."
        )


# ============================================================================
# LOAD DEFAULT DATASET
# ============================================================================

def get_dataset() -> pd.DataFrame:
    """
    Load the configured aircraft maintenance dataset.

    This is kept for:
        - local testing
        - notebooks
        - development
        - backward compatibility

    FastAPI upload requests should normally pass
    the uploaded Excel as a DataFrame directly.
    """

    df = load_dataset()

    _validate_dataframe(
        df
    )

    return df


# ============================================================================
# CHECK AIRCRAFT EXISTS
# ============================================================================

def _check_aircraft_exists(
    df: pd.DataFrame,
    aircraft_id: str,
) -> None:
    """
    Verify that the requested aircraft exists
    in the supplied dataset.
    """

    aircraft_exists = (
        df["Aircraft_ID"]
        .astype(str)
        .eq(aircraft_id)
        .any()
    )

    if not aircraft_exists:
        raise ValueError(
            f"Aircraft '{aircraft_id}' not found in uploaded dataset."
        )


# ============================================================================
# RUN PIPELINE
# ============================================================================

def run_pipeline(
    aircraft_id: str,
    df: pd.DataFrame | None = None,
) -> dict:
    """
    Run the complete Aircraft Maintenance Intelligence pipeline.

    Parameters
    ----------
    aircraft_id : str
        Aircraft identifier, for example:
        "AIR-001"

    df : pandas.DataFrame | None
        Optional dataframe.

        If provided:
            The pipeline uses the uploaded/provided dataframe.

        If None:
            The configured dataset is loaded automatically.

    Returns
    -------
    dict
        Complete maintenance analysis result.

    Examples
    --------

    Using default dataset:

        result = run_pipeline(
            aircraft_id="AIR-001"
        )

    Using uploaded Excel converted to DataFrame:

        result = run_pipeline(
            aircraft_id="AIR-001",
            df=uploaded_df
        )
    """

    # ========================================================================
    # VALIDATE AIRCRAFT ID
    # ========================================================================

    aircraft_id = _validate_aircraft_id(
        aircraft_id
    )

    # ========================================================================
    # LOAD / VALIDATE DATA
    # ========================================================================

    if df is None:
        df = get_dataset()
    else:
        _validate_dataframe(
            df
        )

    # ========================================================================
    # CHECK AIRCRAFT EXISTS
    # ========================================================================

    _check_aircraft_exists(
        df=df,
        aircraft_id=aircraft_id,
    )

    # ========================================================================
    # RUN LANGGRAPH
    # ========================================================================

    result = run_maintenance_analysis(
        aircraft_id=aircraft_id,
        df=df,
    )

    # ========================================================================
    # SAFETY CHECK
    # ========================================================================

    if result is None:
        raise RuntimeError(
            "Maintenance pipeline returned no result."
        )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "Maintenance pipeline returned an invalid result."
        )

    # ========================================================================
    # ADD PIPELINE METADATA
    # ========================================================================

    result["pipeline_version"] = (
        PIPELINE_VERSION
    )

    return result


# ============================================================================
# ANALYZE AIRCRAFT USING DEFAULT DATASET
# ============================================================================

def analyze_aircraft(
    aircraft_id: str,
) -> dict:
    """
    Convenience function for testing/notebooks.

    Uses the configured Excel dataset.
    """

    return run_pipeline(
        aircraft_id=aircraft_id
    )


# ============================================================================
# ANALYZE AIRCRAFT FROM UPLOADED DATAFRAME
# ============================================================================

def analyze_aircraft_from_dataframe(
    aircraft_id: str,
    df: pd.DataFrame,
) -> dict:
    """
    Run the pipeline using a DataFrame supplied by the caller.

    This is the function FastAPI should use after
    reading the uploaded Excel file.

    Example
    -------
    uploaded_df = pd.read_excel(file)

    result = analyze_aircraft_from_dataframe(
        aircraft_id="AIR-001",
        df=uploaded_df,
    )
    """

    _validate_dataframe(
        df
    )

    return run_pipeline(
        aircraft_id=aircraft_id,
        df=df,
    )


# ============================================================================
# ANALYZE ALL AIRCRAFT FROM DATAFRAME
# ============================================================================

def analyze_all_aircraft(
    df: pd.DataFrame | None = None,
) -> dict[str, dict]:
    """
    Analyze every aircraft in the supplied dataset.

    If df is None, the configured dataset is used.

    Returns
    -------
    dict
        {
            "AIR-001": {...},
            "AIR-002": {...},
            ...
        }
    """

    # ========================================================================
    # LOAD DATASET
    # ========================================================================

    if df is None:
        df = get_dataset()
    else:
        _validate_dataframe(
            df
        )

    # ========================================================================
    # GET AIRCRAFT IDS
    # ========================================================================

    aircraft_ids = (
        df["Aircraft_ID"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    # ========================================================================
    # ANALYZE EACH AIRCRAFT
    # ========================================================================

    results: dict[str, dict] = {}

    for aircraft_id in aircraft_ids:

        try:

            results[aircraft_id] = run_pipeline(
                aircraft_id=aircraft_id,
                df=df,
            )

        except Exception as exc:

            results[aircraft_id] = {
                "aircraft": {
                    "aircraft_id": aircraft_id,
                },
                "error": str(exc),
            }

    return results


# ============================================================================
# HEALTH CHECK
# ============================================================================

def pipeline_health() -> dict:
    """
    Basic pipeline health check.

    Used by FastAPI:

        GET /health
    """

    return {
        "status": "ok",
        "pipeline": "Aircraft Maintenance Intelligence",
        "version": PIPELINE_VERSION,
    }


# ============================================================================
# LOCAL TEST
# ============================================================================

if __name__ == "__main__":

    import json

    print("=" * 100)

    print(
        "AIRCRAFT MAINTENANCE INTELLIGENCE PIPELINE TEST"
    )

    print("=" * 100)

    try:

        result = analyze_aircraft(
            "AIR-001"
        )

        print(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

    except Exception as exc:

        print(
            f"\n[PIPELINE ERROR] {exc}"
        )
