# -*- coding: utf-8 -*-

"""
Aircraft Maintenance Data Loader

Responsibilities
----------------
- Load uploaded or configured Excel files
- Normalize Excel column names
- Convert data types
- Validate required columns
- Sort flight records
- Return a clean DataFrame

IMPORTANT
---------
The uploaded Excel may contain columns such as:

    Flight_Cycle (cycles)
    Flight_Cycle_(cycles)
    Flight Cycle (cycles)
    Flight Cycle_(cycles)

Internally, the application ALWAYS uses:

    Flight_Cycle_(cycles)

This prevents column-name mismatch errors between
FastAPI, pipeline, analytics and graph.
"""

import pandas as pd

from src.config import EXCEL_FILE


# ============================================================
# INTERNAL COLUMN SCHEMA
# ============================================================

REQUIRED_COLUMNS = [
    "Aircraft_ID",
    "Flight_Cycle_(cycles)",
]


# ============================================================
# NUMERIC COLUMNS
# ============================================================

NUMERIC_COLUMNS = [
    "Flight_Cycle_(cycles)",
    "Flight_Hours_(hrs)",
    "Cycles_Since_Overhaul_(cycles)",
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


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {
    # --------------------------------------------------------
    # Aircraft ID
    # --------------------------------------------------------
    "Aircraft ID": "Aircraft_ID",
    "Aircraft_ID": "Aircraft_ID",
    "aircraft_id": "Aircraft_ID",

    # --------------------------------------------------------
    # Flight Cycle
    # --------------------------------------------------------
    "Flight Cycle (cycles)": "Flight_Cycle_(cycles)",
    "Flight_Cycle (cycles)": "Flight_Cycle_(cycles)",
    "Flight Cycle_(cycles)": "Flight_Cycle_(cycles)",
    "Flight_Cycle_(cycles)": "Flight_Cycle_(cycles)",
    "Flight_Cycle": "Flight_Cycle_(cycles)",
    "Flight Cycle": "Flight_Cycle_(cycles)",

    # --------------------------------------------------------
    # Flight Hours
    # --------------------------------------------------------
    "Flight Hours (hrs)": "Flight_Hours_(hrs)",
    "Flight_Hours (hrs)": "Flight_Hours_(hrs)",
    "Flight Hours_(hrs)": "Flight_Hours_(hrs)",
    "Flight_Hours_(hrs)": "Flight_Hours_(hrs)",

    # --------------------------------------------------------
    # Cycles Since Overhaul
    # --------------------------------------------------------
    "Cycles Since Overhaul (cycles)": "Cycles_Since_Overhaul_(cycles)",
    "Cycles_Since_Overhaul (cycles)": "Cycles_Since_Overhaul_(cycles)",
    "Cycles Since Overhaul_(cycles)": "Cycles_Since_Overhaul_(cycles)",
    "Cycles_Since_Overhaul_(cycles)": "Cycles_Since_Overhaul_(cycles)",

    # --------------------------------------------------------
    # Temperature / Environment
    # --------------------------------------------------------
    "Ambient Temperature (°C)": "Ambient_Temperature_(°C)",
    "Ambient_Temperature (°C)": "Ambient_Temperature_(°C)",
    "Ambient Temperature_(°C)": "Ambient_Temperature_(°C)",
    "Ambient_Temperature_(°C)": "Ambient_Temperature_(°C)",

    "Humidity (%)": "Humidity_(%)",
    "Humidity_(%)": "Humidity_(%)",

    "Outside Air Temperature (°C)": "Outside_Air_Temperature_(°C)",
    "Outside_Air_Temperature (°C)": "Outside_Air_Temperature_(°C)",
    "Outside Air Temperature_(°C)": "Outside_Air_Temperature_(°C)",
    "Outside_Air_Temperature_(°C)": "Outside_Air_Temperature_(°C)",

    # --------------------------------------------------------
    # Engine
    # --------------------------------------------------------
    "Engine Temperature (°C)": "Engine_Temperature_(°C)",
    "Engine_Temperature (°C)": "Engine_Temperature_(°C)",
    "Engine Temperature_(°C)": "Engine_Temperature_(°C)",
    "Engine_Temperature_(°C)": "Engine_Temperature_(°C)",

    "Exhaust Gas Temperature (°C)": "Exhaust_Gas_Temperature_(°C)",
    "Exhaust_Gas_Temperature (°C)": "Exhaust_Gas_Temperature_(°C)",
    "Exhaust Gas Temperature_(°C)": "Exhaust_Gas_Temperature_(°C)",
    "Exhaust_Gas_Temperature_(°C)": "Exhaust_Gas_Temperature_(°C)",

    "Oil Temperature (°C)": "Oil_Temperature_(°C)",
    "Oil_Temperature (°C)": "Oil_Temperature_(°C)",
    "Oil Temperature_(°C)": "Oil_Temperature_(°C)",
    "Oil_Temperature_(°C)": "Oil_Temperature_(°C)",

    "Oil Pressure (PSI)": "Oil_Pressure_(PSI)",
    "Oil_Pressure (PSI)": "Oil_Pressure_(PSI)",
    "Oil Pressure_(PSI)": "Oil_Pressure_(PSI)",
    "Oil_Pressure_(PSI)": "Oil_Pressure_(PSI)",

    "Engine Vibration (mm/s)": "Engine_Vibration_(mm/s)",
    "Engine_Vibration (mm/s)": "Engine_Vibration_(mm/s)",
    "Engine Vibration_(mm/s)": "Engine_Vibration_(mm/s)",
    "Engine_Vibration_(mm/s)": "Engine_Vibration_(mm/s)",

    "Compressor Pressure (PSI)": "Compressor_Pressure_(PSI)",
    "Compressor_Pressure (PSI)": "Compressor_Pressure_(PSI)",
    "Compressor Pressure_(PSI)": "Compressor_Pressure_(PSI)",
    "Compressor_Pressure_(PSI)": "Compressor_Pressure_(PSI)",

    "Fuel Flow (kg/hr)": "Fuel_Flow_(kg/hr)",
    "Fuel_Flow (kg/hr)": "Fuel_Flow_(kg/hr)",
    "Fuel Flow_(kg/hr)": "Fuel_Flow_(kg/hr)",
    "Fuel_Flow_(kg/hr)": "Fuel_Flow_(kg/hr)",

    "Hydraulic Pressure (PSI)": "Hydraulic_Pressure_(PSI)",
    "Hydraulic_Pressure (PSI)": "Hydraulic_Pressure_(PSI)",
    "Hydraulic Pressure_(PSI)": "Hydraulic_Pressure_(PSI)",
    "Hydraulic_Pressure_(PSI)": "Hydraulic_Pressure_(PSI)",

    "Engine RPM": "Engine_RPM",
    "Engine_RPM": "Engine_RPM",

    "Risk Score (%)": "Risk_Score_(%)",
    "Risk_Score (%)": "Risk_Score_(%)",
    "Risk Score_(%)": "Risk_Score_(%)",
    "Risk_Score_(%)": "Risk_Score_(%)",

    "Remaining Useful Life (cycles)": "Remaining_Useful_Life_(cycles)",
    "Remaining_Useful_Life (cycles)": "Remaining_Useful_Life_(cycles)",
    "Remaining Useful Life_(cycles)": "Remaining_Useful_Life_(cycles)",
    "Remaining_Useful_Life_(cycles)": "Remaining_Useful_Life_(cycles)",

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------
    "Last Maintenance Date": "Last_Maintenance_Date",
    "Last_Maintenance_Date": "Last_Maintenance_Date",
}


# ============================================================
# NORMALIZE SINGLE COLUMN NAME
# ============================================================

def normalize_column_name(column: str) -> str:
    """
    Convert an Excel column name into the application's
    canonical internal column name.
    """

    column = str(column).strip()

    # Direct alias lookup
    if column in COLUMN_ALIASES:
        return COLUMN_ALIASES[column]

    # Generic cleanup
    normalized = (
        column
        .replace(" ", "_")
        .replace("__", "_")
    )

    # Check normalized version against aliases
    if normalized in COLUMN_ALIASES:
        return COLUMN_ALIASES[normalized]

    return normalized


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize all Excel column names.

    Example:

        Flight_Cycle (cycles)
                    ↓
        Flight_Cycle_(cycles)
    """

    df = df.copy()

    original_columns = list(df.columns)

    normalized_columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    df.columns = normalized_columns

    print("\nCOLUMN NORMALIZATION")
    print("-" * 80)

    for original, normalized in zip(
        original_columns,
        normalized_columns,
    ):
        if original != normalized:
            print(
                f"{original!r} -> {normalized!r}"
            )

    print("-" * 80)

    return df


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

def validate_required_columns(
    df: pd.DataFrame,
) -> None:
    """
    Validate columns required by the maintenance pipeline.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Required columns are missing from the uploaded "
            f"Excel file: {missing_columns}. "
            f"Received columns: {list(df.columns)}"
        )


# ============================================================
# CLEAN DATA TYPES
# ============================================================

def clean_data_types(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert date and numeric columns to appropriate
    pandas data types.
    """

    df = df.copy()

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    if "Last_Maintenance_Date" in df.columns:

        df["Last_Maintenance_Date"] = pd.to_datetime(
            df["Last_Maintenance_Date"],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    for column in NUMERIC_COLUMNS:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    return df


# ============================================================
# CLEAN AIRCRAFT IDS
# ============================================================

def clean_aircraft_ids(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean Aircraft_ID values.
    """

    df = df.copy()

    if "Aircraft_ID" in df.columns:

        df["Aircraft_ID"] = (
            df["Aircraft_ID"]
            .astype(str)
            .str.strip()
        )

        # Remove pandas NaN string
        df.loc[
            df["Aircraft_ID"].isin(
                ["nan", "None", ""]
            ),
            "Aircraft_ID",
        ] = pd.NA

    return df


# ============================================================
# SORT FLIGHT RECORDS
# ============================================================

def sort_flight_records(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Sort flight records by aircraft and flight cycle.
    """

    df = df.copy()

    validate_required_columns(df)

    df = (
        df.sort_values(
            [
                "Aircraft_ID",
                "Flight_Cycle_(cycles)",
            ]
        )
        .reset_index(drop=True)
    )

    return df


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(
    file_path=None,
) -> pd.DataFrame:
    """
    Load and prepare aircraft maintenance dataset.

    Parameters
    ----------
    file_path : str | Path | None
        Uploaded Excel path or configured Excel path.

    Returns
    -------
    pandas.DataFrame
        Cleaned and sorted DataFrame.
    """

    path = file_path or EXCEL_FILE

    # --------------------------------------------------------
    # Check file
    # --------------------------------------------------------

    if not path.exists():

        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    # --------------------------------------------------------
    # Read Excel
    # --------------------------------------------------------

    try:

        df = pd.read_excel(path)

    except Exception as exc:

        raise ValueError(
            f"Unable to read Excel file: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Empty check
    # --------------------------------------------------------

    if df.empty:

        raise ValueError(
            "Aircraft maintenance dataset is empty."
        )

    # --------------------------------------------------------
    # Normalize columns
    # --------------------------------------------------------

    df = clean_column_names(df)

    # --------------------------------------------------------
    # Validate columns
    # --------------------------------------------------------

    validate_required_columns(df)

    # --------------------------------------------------------
    # Clean IDs
    # --------------------------------------------------------

    df = clean_aircraft_ids(df)

    # --------------------------------------------------------
    # Clean data types
    # --------------------------------------------------------

    df = clean_data_types(df)

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = sort_flight_records(df)

    return df


# ============================================================
# PREPARE UPLOADED DATAFRAME
# ============================================================

def prepare_uploaded_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare a DataFrame received directly from FastAPI.

    IMPORTANT:
    This function does NOT read from disk.

    It performs exactly the same cleaning and normalization
    as load_dataset().
    """

    if df is None:

        raise ValueError(
            "Uploaded dataset cannot be None."
        )

    if not isinstance(
        df,
        pd.DataFrame,
    ):

        raise TypeError(
            "Uploaded dataset must be a pandas DataFrame."
        )

    if df.empty:

        raise ValueError(
            "Uploaded Excel file contains no data."
        )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    df = clean_column_names(df)

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_required_columns(df)

    # --------------------------------------------------------
    # Clean IDs
    # --------------------------------------------------------

    df = clean_aircraft_ids(df)

    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------

    df = clean_data_types(df)

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = sort_flight_records(df)

    return df


# ============================================================
# DATASET SUMMARY
# ============================================================

def get_dataset_summary(
    df: pd.DataFrame,
) -> dict:
    """
    Return basic information about the dataset.
    """

    return {
        "rows": len(df),

        "columns": len(df.columns),

        "aircraft_count": (
            df["Aircraft_ID"].nunique()
            if "Aircraft_ID" in df.columns
            else 0
        ),

        "aircraft_ids": (
            df["Aircraft_ID"]
            .dropna()
            .unique()
            .tolist()
            if "Aircraft_ID" in df.columns
            else []
        ),
    }