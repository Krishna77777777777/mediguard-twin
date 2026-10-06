from __future__ import annotations

from ..models import RiskLevel, SandboxResult, SandboxStep, SandboxStopCase
from .safety import analyze_risks
from .timeline import timeline_for_30_days

STOP_KEYWORDS = {
    "anaphylaxis": "allergy conflict",
    "major bleeding": "drug-drug interaction",
    "respiratory/CNS depression": "dependence risk",
    "QT/arrhythmia risk": "drug-drug interaction",
    "renal/hepatic accumulation": "drug-disease interaction",
    "overdose/dose concern": "dose concern",
    "duplicate therapy": "duplicate ingredient",
    "high dependence risk": "dependence risk",
}


def run_sandbox(patient, prescription) -> SandboxResult:
    timeline = timeline_for_30_days(
        patient.current_medications,
        patient.recently_stopped_medications,
        prescription,
        patient.adverse_reactions,
    )
    findings = analyze_risks(patient, prescription, timeline)

    steps = [
        SandboxStep(day=0, summary="Simulation starts with proposed prescription and baseline patient profile."),
        SandboxStep(day=1, summary="Evaluate immediate interaction and allergy rules."),
        SandboxStep(day=2, summary="Evaluate residual exposure from 30-day medication history."),
        SandboxStep(day=3, summary="Evaluate organ function and dose accumulation concerns."),
    ]

    stop_cases: list[SandboxStopCase] = []
    for finding in findings:
        if finding.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            for label, category in STOP_KEYWORDS.items():
                if category == finding.category:
                    stop_cases.append(
                        SandboxStopCase(
                            code=label.upper().replace("/", "_").replace(" ", "_"),
                            reason=f"{label} stop case triggered by: {finding.title}",
                            risk_level=finding.risk_level,
                        )
                    )

    if stop_cases:
        steps.append(
            SandboxStep(
                day=4,
                summary="Simulation stopped due to high-risk stop case(s).",
                triggered_flags=[s.code for s in stop_cases],
            )
        )
        recommendation = (
            "STOP SIMULATION — clinician review required before proceeding with this medication scenario."
        )
    else:
        steps.append(
            SandboxStep(day=4, summary="No high-risk stop case fired in current rules. Continue clinician-led review.")
        )
        recommendation = "No hard stop in seeded rules; continue only with clinician-supervised decision making."

    return SandboxResult(
        steps=steps,
        stop_cases=stop_cases,
        final_recommendation=recommendation,
        disclaimer=(
            "This virtual-patient sandbox is a deterministic decision-support simulation and not a biological guarantee. "
            "Do not use as a sole basis for prescribing decisions."
        ),
    )
