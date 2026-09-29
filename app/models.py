from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Frequency(str, Enum):
    DAILY = "daily"
    BID = "bid"
    TID = "tid"
    QID = "qid"
    WEEKLY = "weekly"
    PRN = "prn"


class OrganIndicators(BaseModel):
    egfr: Optional[float] = None
    alt: Optional[float] = None
    ast: Optional[float] = None
    hepatic_impairment: Optional[bool] = None


class Allergy(BaseModel):
    substance: str
    reaction: str
    severity: Optional[str] = None


class AdverseReaction(BaseModel):
    date: date
    suspected_drug: str
    symptom: str


class MedicationRecord(BaseModel):
    drug_name: str
    ingredient: str
    therapeutic_class: str
    strength: Optional[str] = None
    dose: float
    unit: str
    route: str
    frequency: Frequency
    start_date: date
    duration_days: int = Field(ge=1, le=365)
    indication: Optional[str] = None


class PatientProfile(BaseModel):
    id: str
    name: str
    age: int = Field(ge=0, le=120)
    weight_kg: float = Field(gt=0)
    pregnancy_status: Optional[bool] = None
    allergies: List[Allergy] = Field(default_factory=list)
    diagnoses: List[str] = Field(default_factory=list)
    organ_indicators: OrganIndicators = Field(default_factory=OrganIndicators)
    current_medications: List[MedicationRecord] = Field(default_factory=list)
    recently_stopped_medications: List[MedicationRecord] = Field(default_factory=list)
    adverse_reactions: List[AdverseReaction] = Field(default_factory=list)


class PrescriptionInput(BaseModel):
    drug_name: str
    ingredient: str
    strength: str
    dose: float
    unit: str
    route: str
    frequency: Frequency
    start_date: date
    duration_days: int = Field(ge=1, le=365)
    indication: str


class TimelineEntry(BaseModel):
    drug_name: str
    ingredient: str
    therapeutic_class: str
    start_date: date
    stop_date: date
    currently_active: bool
    recently_stopped: bool
    days_since_last_dose: Optional[int]
    recent_exposure: bool
    overlap_with_new_rx_days: int = 0


class RiskFinding(BaseModel):
    category: str
    title: str
    risk_level: RiskLevel
    confidence: float = Field(ge=0, le=1)
    evidence_source: str
    patient_facts_used: List[str]
    mechanism: str
    recommended_clinician_action: str
    uncertainty_notes: Optional[str] = None


class AnalysisResult(BaseModel):
    patient_id: str
    prescription: PrescriptionInput
    timeline: List[TimelineEntry]
    findings: List[RiskFinding]
    highest_risk: RiskLevel
    disclaimer: str


class SandboxStopCase(BaseModel):
    code: str
    reason: str
    risk_level: RiskLevel


class SandboxStep(BaseModel):
    day: int
    summary: str
    triggered_flags: List[str] = Field(default_factory=list)


class SandboxRequest(BaseModel):
    patient: PatientProfile
    prescription: PrescriptionInput


class SandboxResult(BaseModel):
    mode: str = "decision-support simulation"
    steps: List[SandboxStep]
    stop_cases: List[SandboxStopCase]
    final_recommendation: str
    disclaimer: str
