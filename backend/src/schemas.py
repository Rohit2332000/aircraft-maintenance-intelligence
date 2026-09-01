# -*- coding: utf-8 -*-

"""
Pydantic schemas for the Aircraft Maintenance Intelligence API.

Flow:

Analytics
    +
Maintenance Manual Retriever
    ↓
LLM
    ↓
ParameterAnalysis
    ↓
AircraftAnalysis
    ↓
FastAPI JSON response
"""

from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# HISTORICAL ANALYTICS
# ============================================================================

class HistoricalAnalytics(BaseModel):
    count: int = 0

    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None

    minimum: Optional[float] = None
    maximum: Optional[float] = None


# ============================================================================
# PARAMETER ANALYTICS
# ============================================================================

class ParameterAnalytics(BaseModel):

    latest_value: Optional[float] = None

    historical: HistoricalAnalytics

    difference_from_mean: Optional[float] = None
    percentage_change: Optional[float] = None

    z_score: Optional[float] = None

    trend_slope: Optional[float] = None
    trend: str = "UNKNOWN"

    statistical_anomaly: bool = False
    statistical_status: str = "NORMAL"


# ============================================================================
# MANUAL CLASSIFICATION
# ============================================================================

class ManualClassification(BaseModel):

    status: str = "UNKNOWN"

    normal_range: Optional[list[float]] = None

    recommended_action: Optional[str] = None

    source: Optional[str] = None

    manual_evidence_available: bool = False


# ============================================================================
# FAILURE MODE
# ============================================================================

class FailureMode(BaseModel):

    name: Optional[str] = None

    symptoms: list[str] = Field(
        default_factory=list
    )

    causes: list[str] = Field(
        default_factory=list
    )

    parameters: list[str] = Field(
        default_factory=list
    )


# ============================================================================
# MAINTENANCE ANALYSIS
# ============================================================================

class MaintenanceAnalysis(BaseModel):

    maintenance_required: bool = False

    priority: str = "LOW"

    recommended_action: Optional[str] = None

    reasoning: Optional[str] = None

    failure_modes: list[FailureMode] = Field(
        default_factory=list
    )

    confidence: str = "LOW"

    manual_sources: list[str] = Field(
        default_factory=list
    )


# ============================================================================
# PARAMETER RESULT
# ============================================================================

class ParameterAnalysis(BaseModel):

    parameter: str

    display_name: Optional[str] = None

    unit: Optional[str] = None

    analytics: ParameterAnalytics

    manual: ManualClassification

    maintenance: MaintenanceAnalysis


# ============================================================================
# AIRCRAFT SUMMARY
# ============================================================================

class AircraftSummary(BaseModel):

    aircraft_id: str

    flight_cycle: int

    risk_score: Optional[float] = None

    remaining_useful_life: Optional[float] = None

    overall_status: str = "NORMAL"

    parameters_analyzed: int = 0

    anomalies_detected: int = 0

    maintenance_required_count: int = 0


# ============================================================================
# FINAL AIRCRAFT RESPONSE
# ============================================================================

class AircraftAnalysisResponse(BaseModel):

    aircraft: AircraftSummary

    parameters: list[ParameterAnalysis] = Field(
        default_factory=list
    )