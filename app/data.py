from __future__ import annotations

from datetime import date, timedelta

from .models import (
    AdverseReaction,
    Allergy,
    Frequency,
    MedicationRecord,
    OrganIndicators,
    PatientProfile,
)

DISCLAIMER = (
    "MediGuard Twin is a clinical decision-support prototype for education and "
    "workflow support. It is not medical advice and does not replace a licensed clinician. "
    "All recommendations require clinician review."
)

PROVIDER_ADAPTERS = {
    "rxnorm": "Adapter interface prepared for concept normalization (not required for demo runtime)",
    "who_atc": "Adapter interface prepared for class/DDD enrichment",
    "openfda_dailymed": "Adapter interface prepared for label warnings and evidence links",
    "ema": "Adapter interface prepared for EEA product information",
}

KNOWLEDGE_BASE_VERSION = "2026.09-demo"

DRUG_CATALOG = {
    "warfarin": {
        "ingredient": "warfarin",
        "therapeutic_class": "anticoagulant",
        "dose_limits_mg_per_day": 10,
        "dependence_risk": False,
    },
    "ibuprofen": {
        "ingredient": "ibuprofen",
        "therapeutic_class": "nsaid",
        "dose_limits_mg_per_day": 2400,
        "dependence_risk": False,
    },
    "diazepam": {
        "ingredient": "diazepam",
        "therapeutic_class": "benzodiazepine",
        "dose_limits_mg_per_day": 20,
        "dependence_risk": True,
    },
    "amoxicillin": {
        "ingredient": "amoxicillin",
        "therapeutic_class": "penicillin",
        "dose_limits_mg_per_day": 3000,
        "dependence_risk": False,
    },
    "metformin": {
        "ingredient": "metformin",
        "therapeutic_class": "biguanide",
        "dose_limits_mg_per_day": 2550,
        "dependence_risk": False,
    },
    "paracetamol": {
        "ingredient": "acetaminophen",
        "therapeutic_class": "analgesic",
        "dose_limits_mg_per_day": 4000,
        "dependence_risk": False,
    },
    "lorazepam": {
        "ingredient": "lorazepam",
        "therapeutic_class": "benzodiazepine",
        "dose_limits_mg_per_day": 8,
        "dependence_risk": True,
    },
}

INTERACTION_RULES = [
    {
        "ingredients": {"warfarin", "ibuprofen"},
        "risk_level": "CRITICAL",
        "mechanism": "Additive bleeding risk via anticoagulant + NSAID effect",
        "evidence": "Seeded demo rule aligned to common label warnings (FDA/EMA class-level)",
        "action": "Avoid combination or perform urgent clinician review with bleeding monitoring.",
    },
    {
        "ingredients": {"diazepam", "lorazepam"},
        "risk_level": "HIGH",
        "mechanism": "Additive CNS/respiratory depression with duplicate benzodiazepines",
        "evidence": "Seeded demo rule, benzodiazepine class warning",
        "action": "Avoid duplicate sedative therapy; taper/alternative required.",
    },
]

DISEASE_RULES = [
    {
        "ingredient": "ibuprofen",
        "diagnosis_match": "chronic kidney disease",
        "risk_level": "HIGH",
        "mechanism": "NSAID may reduce renal perfusion and worsen CKD",
        "evidence": "Seeded demo disease interaction",
        "action": "Prefer alternative analgesic and check renal function.",
    },
    {
        "ingredient": "diazepam",
        "diagnosis_match": "sleep apnea",
        "risk_level": "HIGH",
        "mechanism": "Sedative can increase respiratory depression risk",
        "evidence": "Seeded demo disease interaction",
        "action": "Avoid or tightly monitor in vulnerable patients.",
    },
]

ALLERGY_CLASS_MAP = {
    "penicillin": {"penicillin", "amoxicillin", "ampicillin"},
    "nsaid": {"ibuprofen", "naproxen", "diclofenac"},
}

EVIDENCE_SOURCES = {
    "seed_notice": "Seed dataset for MVP demo only; not exhaustive.",
    "integration_note": "Production integration targets: RxNorm, WHO ATC/DDD, FDA/openFDA/DailyMed, EMA.",
}


def _days_ago(days: int) -> date:
    return date.today() - timedelta(days=days)


DEMO_PATIENTS = {
    "high-risk-renal": PatientProfile(
        id="high-risk-renal",
        name="Ravi Kumar",
        age=68,
        weight_kg=82,
        pregnancy_status=False,
        allergies=[Allergy(substance="penicillin", reaction="anaphylaxis", severity="severe")],
        diagnoses=["chronic kidney disease", "hypertension", "type 2 diabetes"],
        organ_indicators=OrganIndicators(egfr=35, alt=28, ast=30, hepatic_impairment=False),
        current_medications=[
            MedicationRecord(
                drug_name="Warfarin",
                ingredient="warfarin",
                therapeutic_class="anticoagulant",
                strength="5 mg",
                dose=5,
                unit="mg",
                route="oral",
                frequency=Frequency.DAILY,
                start_date=_days_ago(20),
                duration_days=60,
                indication="stroke prophylaxis",
            )
        ],
        recently_stopped_medications=[
            MedicationRecord(
                drug_name="Diazepam",
                ingredient="diazepam",
                therapeutic_class="benzodiazepine",
                strength="5 mg",
                dose=5,
                unit="mg",
                route="oral",
                frequency=Frequency.BID,
                start_date=_days_ago(18),
                duration_days=10,
                indication="anxiety",
            )
        ],
        adverse_reactions=[
            AdverseReaction(
                date=_days_ago(8), suspected_drug="diazepam", symptom="dizziness and drowsiness"
            )
        ],
    ),
    "lower-risk": PatientProfile(
        id="lower-risk",
        name="Meera Singh",
        age=34,
        weight_kg=64,
        pregnancy_status=False,
        allergies=[Allergy(substance="sulfa", reaction="rash", severity="moderate")],
        diagnoses=["tension headache"],
        organ_indicators=OrganIndicators(egfr=105, alt=18, ast=20, hepatic_impairment=False),
        current_medications=[
            MedicationRecord(
                drug_name="Paracetamol",
                ingredient="acetaminophen",
                therapeutic_class="analgesic",
                strength="500 mg",
                dose=500,
                unit="mg",
                route="oral",
                frequency=Frequency.BID,
                start_date=_days_ago(3),
                duration_days=5,
                indication="headache",
            )
        ],
        recently_stopped_medications=[],
        adverse_reactions=[],
    ),
}
