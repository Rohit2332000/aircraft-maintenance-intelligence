# -*- coding: utf-8 -*-

"""
FastAPI entry point for Aircraft Maintenance Intelligence.

FLOW
----
User
    |
    | Upload Excel + Aircraft ID
    v
FastAPI
    |
    | Read Excel
    | Normalize column names
    v
pandas DataFrame
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
    |
    v
JSON Response
"""
from dotenv import load_dotenv
from io import BytesIO
import traceback

import pandas as pd

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
)

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from src.pipeline import (
    run_pipeline,
    pipeline_health,
)


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Aircraft Maintenance Intelligence API",
    description=(
        "AI-powered aircraft maintenance analysis using "
        "historical analytics, maintenance-manual retrieval, "
        "and LLM-based maintenance recommendations."
    ),
    version="1.2.0",
)


# ============================================================================
# CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# COLUMN NORMALIZATION
# ============================================================================

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize uploaded Excel column names so they exactly match
    the column names expected by analytics.py.

    Example:

        Flight_Cycle (cycles)
            ->
        Flight_Cycle_(cycles)

    The analytics module expects parentheses to be connected
    to the column name with an underscore.
    """

    df = df.copy()

    # ------------------------------------------------------------------------
    # Convert all column names to strings
    # ------------------------------------------------------------------------

    df.columns = df.columns.astype(str)

    # ------------------------------------------------------------------------
    # Remove leading/trailing whitespace
    # ------------------------------------------------------------------------

    df.columns = df.columns.str.strip()

    # ------------------------------------------------------------------------
    # Replace spaces with underscores
    # ------------------------------------------------------------------------

    df.columns = df.columns.str.replace(
        " ",
        "_",
        regex=False,
    )

    # ------------------------------------------------------------------------
    # Normalize the exact column format used by analytics.py
    #
    # Example:
    #
    # Flight_Cycle_(cycles)
    # Flight_Hours_(hrs)
    # Ambient_Temperature_(°C)
    #
    # Some uploaded Excel files contain:
    #
    # Flight_Cycle_(cycles)  -> already correct
    #
    # Others contain:
    #
    # Flight_Cycle_(cycles)  -> same
    #
    # And the problematic file may contain:
    #
    # Flight_Cycle_(cycles)
    #
    # after pandas processing.
    # ------------------------------------------------------------------------

    column_aliases = {
        "Flight_Cycle_(cycles)": "Flight_Cycle_(cycles)",
        "Flight_Cycle_(Cycles)": "Flight_Cycle_(cycles)",
        "Flight_Hours_(hrs)": "Flight_Hours_(hrs)",
        "Cycles_Since_Overhaul_(cycles)": "Cycles_Since_Overhaul_(cycles)",
        "Ambient_Temperature_(°C)": "Ambient_Temperature_(°C)",
        "Humidity_(%)": "Humidity_(%)",
        "Outside_Air_Temperature_(°C)": "Outside_Air_Temperature_(°C)",
        "Engine_Temperature_(°C)": "Engine_Temperature_(°C)",
        "Exhaust_Gas_Temperature_(°C)": "Exhaust_Gas_Temperature_(°C)",
        "Oil_Temperature_(°C)": "Oil_Temperature_(°C)",
        "Oil_Pressure_(PSI)": "Oil_Pressure_(PSI)",
        "Engine_Vibration_(mm/s)": "Engine_Vibration_(mm/s)",
        "Compressor_Pressure_(PSI)": "Compressor_Pressure_(PSI)",
        "Fuel_Flow_(kg/hr)": "Fuel_Flow_(kg/hr)",
        "Hydraulic_Pressure_(PSI)": "Hydraulic_Pressure_(PSI)",
        "Engine_RPM": "Engine_RPM",
        "Risk_Score_(%)": "Risk_Score_(%)",
        "Remaining_Useful_Life_(cycles)": "Remaining_Useful_Life_(cycles)",
    }

    df = df.rename(
        columns=column_aliases
    )

    return df


# ============================================================================
# REQUIRED COLUMNS
# ============================================================================

REQUIRED_COLUMNS = [
    "Aircraft_ID",
    "Flight_Cycle_(cycles)",
]


# ============================================================================
# ROOT
# ============================================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Aircraft Maintenance Intelligence API",
        "version": "1.2.0",
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health():
    return pipeline_health()


# ============================================================================
# AIRCRAFT ANALYSIS
# ============================================================================

@app.post(
    "/api/v1/aircraft/{aircraft_id}/analysis"
)
async def analyze_aircraft(
    aircraft_id: str,
    file: UploadFile = File(...),
):
    """
    Run complete maintenance analysis for one aircraft
    using a user-uploaded Excel file.

    The Excel file is:

        1. Uploaded by user
        2. Read into pandas
        3. Column names normalized
        4. Data types cleaned
        5. Passed directly to pipeline.py

    The uploaded file is NOT permanently saved.
    """

    # ========================================================================
    # VALIDATE AIRCRAFT ID
    # ========================================================================

    if not aircraft_id or not aircraft_id.strip():
        raise HTTPException(
            status_code=400,
            detail="aircraft_id is required.",
        )

    aircraft_id = aircraft_id.strip()

    # ========================================================================
    # VALIDATE FILE
    # ========================================================================

    if file is None:
        raise HTTPException(
            status_code=400,
            detail="Excel file is required.",
        )

    filename = file.filename or ""

    # ========================================================================
    # VALIDATE FILE EXTENSION
    # ========================================================================

    if not filename.lower().endswith(
        (".xlsx", ".xls")
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. "
                "Please upload an Excel file (.xlsx or .xls)."
            ),
        )

    # ========================================================================
    # READ EXCEL
    # ========================================================================

    try:

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded Excel file is empty.",
            )

        df = pd.read_excel(
            BytesIO(file_bytes)
        )

    except HTTPException:
        raise

    except Exception as exc:

        print("=" * 100)
        print("[EXCEL READ ERROR]")
        print(f"File: {filename}")
        print(f"Error: {exc}")
        traceback.print_exc()
        print("=" * 100)

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to read the uploaded Excel file. "
                "Please upload a valid Excel workbook."
            ),
        )

    # ========================================================================
    # CHECK EMPTY DATASET
    # ========================================================================

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Uploaded Excel file contains no data.",
        )

    # ========================================================================
    # SHOW ORIGINAL COLUMNS
    # ========================================================================

    print("=" * 100)
    print("ORIGINAL EXCEL COLUMNS")
    print("=" * 100)

    for column in df.columns:
        print(repr(column))

    # ========================================================================
    # NORMALIZE COLUMN NAMES
    # ========================================================================

    df = normalize_column_names(df)

    # ========================================================================
    # SHOW NORMALIZED COLUMNS
    # ========================================================================

    print("=" * 100)
    print("NORMALIZED EXCEL COLUMNS")
    print("=" * 100)

    for column in df.columns:
        print(repr(column))

    # ========================================================================
    # VALIDATE REQUIRED COLUMNS
    # ========================================================================

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Required columns are missing "
                    "from the uploaded Excel file."
                ),
                "missing_columns": missing_columns,
                "received_columns": df.columns.tolist(),
            },
        )

    # ========================================================================
    # CLEAN AIRCRAFT IDS
    # ========================================================================

    df["Aircraft_ID"] = (
        df["Aircraft_ID"]
        .astype(str)
        .str.strip()
    )

    # ========================================================================
    # CLEAN FLIGHT CYCLE
    # ========================================================================

    df["Flight_Cycle_(cycles)"] = pd.to_numeric(
        df["Flight_Cycle_(cycles)"],
        errors="coerce",
    )

    # ========================================================================
    # CHECK INVALID FLIGHT CYCLES
    # ========================================================================

    if df["Flight_Cycle_(cycles)"].isna().all():

        raise HTTPException(
            status_code=400,
            detail=(
                "Column 'Flight_Cycle_(cycles)' "
                "does not contain valid numeric values."
            ),
        )

    # ========================================================================
    # CHECK AIRCRAFT EXISTS
    # ========================================================================

    aircraft_exists = (
        df["Aircraft_ID"]
        .eq(aircraft_id)
        .any()
    )

    if not aircraft_exists:

        available_aircraft = (
            df["Aircraft_ID"]
            .replace("nan", pd.NA)
            .dropna()
            .unique()
            .tolist()
        )

        raise HTTPException(
            status_code=404,
            detail={
                "message": (
                    f"Aircraft '{aircraft_id}' "
                    "was not found in the uploaded dataset."
                ),
                "available_aircraft": available_aircraft,
            },
        )

    # ========================================================================
    # RUN PIPELINE
    # ========================================================================

    try:

        print("=" * 100)
        print("AIRCRAFT MAINTENANCE ANALYSIS")
        print("=" * 100)

        print(f"Aircraft ID   : {aircraft_id}")
        print(f"Uploaded File : {filename}")
        print(f"Rows          : {len(df)}")
        print(f"Columns       : {len(df.columns)}")

        print("=" * 100)
        print("DATAFRAME COLUMNS SENT TO PIPELINE")
        print("=" * 100)

        print(df.columns.tolist())

        print("=" * 100)

        # --------------------------------------------------------------------
        # IMPORTANT
        #
        # We pass df directly.
        #
        # pipeline.py:
        #
        # run_pipeline(
        #     aircraft_id=aircraft_id,
        #     df=df
        # )
        #
        # Therefore pipeline.py will NOT call get_dataset()
        # and will NOT load the old saved Excel.
        # --------------------------------------------------------------------

        result = run_pipeline(
            aircraft_id=aircraft_id,
            df=df,
        )

        # ====================================================================
        # VALIDATE RESULT
        # ====================================================================

        if result is None:
            raise RuntimeError(
                "Pipeline returned no result."
            )

        if not isinstance(result, dict):
            raise TypeError(
                "Pipeline returned an invalid result."
            )

        return result

    # ========================================================================
    # VALIDATION ERROR
    # ========================================================================

    except ValueError as exc:

        print("=" * 100)
        print("[PIPELINE VALIDATION ERROR]")
        print(f"Aircraft: {aircraft_id}")
        print(f"Error: {exc}")
        print("=" * 100)

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # ========================================================================
    # REQUIRED FILE ERROR
    # ========================================================================

    except FileNotFoundError as exc:

        print("=" * 100)
        print("[SYSTEM FILE ERROR]")
        print(f"Aircraft: {aircraft_id}")
        print(f"Error: {exc}")

        traceback.print_exc()

        print("=" * 100)

        raise HTTPException(
            status_code=500,
            detail=(
                f"Required system file not found: {exc}"
            ),
        )

    # ========================================================================
    # UNEXPECTED ERROR
    # ========================================================================

    except Exception as exc:

        print("=" * 100)
        print("[API ERROR]")
        print(f"Aircraft: {aircraft_id}")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error: {exc}")
        print("=" * 100)

        traceback.print_exc()

        print("=" * 100)

        raise HTTPException(
            status_code=500,
            detail=(
                f"Aircraft maintenance analysis failed: {str(exc)}"
            ),
        )


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )