from datetime import date

from app.data import DEMO_PATIENTS
from app.models import Frequency, PrescriptionInput, RiskLevel
from app.services.safety import analyze_risks, highest_risk
from app.services.timeline import timeline_for_30_days


def test_high_risk_patient_gets_critical_interaction():
    patient = DEMO_PATIENTS["high-risk-renal"]
    rx = PrescriptionInput(
        drug_name="Ibuprofen",
        ingredient="ibuprofen",
        strength="400 mg",
        dose=400,
        unit="mg",
        route="oral",
        frequency=Frequency.TID,
        start_date=date.today(),
        duration_days=5,
        indication="pain",
    )

    timeline = timeline_for_30_days(patient.current_medications, patient.recently_stopped_medications, rx)
    findings = analyze_risks(patient, rx, timeline)

    assert any(f.category == "drug-drug interaction" and f.risk_level == RiskLevel.CRITICAL for f in findings)
    assert highest_risk(findings) == RiskLevel.CRITICAL


def test_lower_risk_patient_falls_back_to_low_or_moderate():
    patient = DEMO_PATIENTS["lower-risk"]
    rx = PrescriptionInput(
        drug_name="Paracetamol",
        ingredient="acetaminophen",
        strength="500 mg",
        dose=500,
        unit="mg",
        route="oral",
        frequency=Frequency.DAILY,
        start_date=date.today(),
        duration_days=3,
        indication="headache",
    )

    timeline = timeline_for_30_days(patient.current_medications, patient.recently_stopped_medications, rx)
    findings = analyze_risks(patient, rx, timeline)
    assert highest_risk(findings) in {RiskLevel.LOW, RiskLevel.MODERATE}
