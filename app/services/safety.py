from __future__ import annotations

from collections import defaultdict

from ..data import ALLERGY_CLASS_MAP, DISEASE_RULES, DRUG_CATALOG, INTERACTION_RULES
from ..models import PatientProfile, PrescriptionInput, RiskFinding, RiskLevel, TimelineEntry

RISK_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MODERATE: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}

FREQ_PER_DAY = {
    "daily": 1,
    "bid": 2,
    "tid": 3,
    "qid": 4,
    "weekly": 1 / 7,
    "prn": 1,
}


def _mk_finding(
    *,
    category: str,
    title: str,
    level: RiskLevel,
    confidence: float,
    evidence: str,
    facts: list[str],
    mechanism: str,
    action: str,
    uncertainty: str | None = None,
) -> RiskFinding:
    return RiskFinding(
        category=category,
        title=title,
        risk_level=level,
        confidence=confidence,
        evidence_source=evidence,
        patient_facts_used=facts,
        mechanism=mechanism,
        recommended_clinician_action=action,
        uncertainty_notes=uncertainty,
    )


def analyze_risks(
    patient: PatientProfile,
    prescription: PrescriptionInput,
    timeline: list[TimelineEntry],
) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    rx_ingredient = prescription.ingredient.lower()
    rx_class = DRUG_CATALOG.get(rx_ingredient, {}).get("therapeutic_class")

    # DDI with active/recent medications
    for entry in timeline:
        pair = {entry.ingredient.lower(), rx_ingredient}
        for rule in INTERACTION_RULES:
            if pair == rule["ingredients"]:
                findings.append(
                    _mk_finding(
                        category="drug-drug interaction",
                        title=f"{entry.ingredient.title()} + {rx_ingredient.title()} interaction",
                        level=RiskLevel(rule["risk_level"]),
                        confidence=0.9 if entry.currently_active else 0.78,
                        evidence=rule["evidence"],
                        facts=[
                            f"Recent medication: {entry.drug_name}",
                            f"Overlap days with new Rx: {entry.overlap_with_new_rx_days}",
                        ],
                        mechanism=rule["mechanism"],
                        action=rule["action"],
                        uncertainty="Consider INR/lab and indication context not fully modeled.",
                    )
                )

    # Drug-disease interactions
    diag_lower = {d.lower() for d in patient.diagnoses}
    for rule in DISEASE_RULES:
        if rule["ingredient"] == rx_ingredient and rule["diagnosis_match"] in diag_lower:
            findings.append(
                _mk_finding(
                    category="drug-disease interaction",
                    title=f"{rx_ingredient.title()} concern with {rule['diagnosis_match']}",
                    level=RiskLevel(rule["risk_level"]),
                    confidence=0.84,
                    evidence=rule["evidence"],
                    facts=[f"Diagnosis: {rule['diagnosis_match']}", f"eGFR: {patient.organ_indicators.egfr}"],
                    mechanism=rule["mechanism"],
                    action=rule["action"],
                )
            )

    # Duplicate ingredient/class
    for entry in timeline:
        if entry.currently_active and entry.ingredient.lower() == rx_ingredient:
            findings.append(
                _mk_finding(
                    category="duplicate ingredient",
                    title="Same active ingredient already active",
                    level=RiskLevel.HIGH,
                    confidence=0.92,
                    evidence="Timeline + active medication comparison",
                    facts=[f"Current active ingredient: {entry.ingredient}"],
                    mechanism="Ingredient duplication can cause overdose",
                    action="Verify medication reconciliation and discontinue duplicate order.",
                )
            )
            break

    if rx_class:
        for entry in timeline:
            if entry.currently_active and entry.therapeutic_class == rx_class and entry.ingredient.lower() != rx_ingredient:
                findings.append(
                    _mk_finding(
                        category="therapeutic class duplication",
                        title=f"Potential duplicate class: {rx_class}",
                        level=RiskLevel.MODERATE,
                        confidence=0.74,
                        evidence="Therapeutic class overlap check",
                        facts=[f"Active {entry.drug_name} class={entry.therapeutic_class}"],
                        mechanism="Additive pharmacodynamic effects within class",
                        action="Review need for dual therapy and monitor adverse effects.",
                    )
                )
                break

    # Dose/frequency checks
    max_daily = DRUG_CATALOG.get(rx_ingredient, {}).get("dose_limits_mg_per_day")
    if max_daily and prescription.unit.lower() == "mg":
        daily = prescription.dose * FREQ_PER_DAY[prescription.frequency.value]
        if daily > max_daily:
            findings.append(
                _mk_finding(
                    category="dose concern",
                    title="Dose exceeds configured daily limit",
                    level=RiskLevel.HIGH,
                    confidence=0.86,
                    evidence="Dose limit from seeded knowledge base",
                    facts=[f"Calculated daily dose: {daily:.1f} mg", f"Configured max: {max_daily} mg/day"],
                    mechanism="Potential overdose/toxicity due to high total daily exposure",
                    action="Hold order and adjust dose/frequency with clinician review.",
                )
            )

    # Allergy conflicts and cross-reactivity
    allergy_substances = {a.substance.lower() for a in patient.allergies}
    if rx_ingredient in allergy_substances:
        findings.append(
            _mk_finding(
                category="allergy conflict",
                title="Exact ingredient allergy conflict",
                level=RiskLevel.CRITICAL,
                confidence=0.97,
                evidence="Patient allergy profile",
                facts=[f"Allergy includes {rx_ingredient}", "Recorded severe reaction history"],
                mechanism="Re-exposure to known allergen can trigger anaphylaxis",
                action="Do not prescribe; urgent alternative required.",
            )
        )

    for allergy in allergy_substances:
        members = ALLERGY_CLASS_MAP.get(allergy, set())
        if rx_ingredient in members and rx_ingredient != allergy:
            findings.append(
                _mk_finding(
                    category="cross-reactivity",
                    title="Potential class cross-reactivity",
                    level=RiskLevel.HIGH,
                    confidence=0.8,
                    evidence="Seeded allergy class map",
                    facts=[f"Allergy class: {allergy}", f"Requested ingredient: {rx_ingredient}"],
                    mechanism="Shared class may trigger related hypersensitivity response",
                    action="Clinician/allergy specialist review before prescribing.",
                    uncertainty="Cross-reactivity probability varies by individual and compound.",
                )
            )

    # Recent residual/overlap
    for entry in timeline:
        if entry.recently_stopped and entry.overlap_with_new_rx_days > 0:
            findings.append(
                _mk_finding(
                    category="recent exposure overlap",
                    title=f"Recent exposure to {entry.ingredient}",
                    level=RiskLevel.MODERATE,
                    confidence=0.7,
                    evidence="30-day timeline residual exposure rule",
                    facts=[f"Days since last dose: {entry.days_since_last_dose}", f"Overlap days: {entry.overlap_with_new_rx_days}"],
                    mechanism="Residual pharmacodynamic effect may persist after stop",
                    action="Assess washout adequacy and monitor early therapy period.",
                )
            )

    # Dependence/misuse risk
    if DRUG_CATALOG.get(rx_ingredient, {}).get("dependence_risk"):
        prior_dependence_exposure = sum(
            1 for t in timeline if t.therapeutic_class in {"benzodiazepine", "opioid"}
        )
        level = RiskLevel.HIGH if prior_dependence_exposure else RiskLevel.MODERATE
        findings.append(
            _mk_finding(
                category="dependence risk",
                title="Dependence/misuse/withdrawal risk flag",
                level=level,
                confidence=0.76,
                evidence="Dependence-associated class heuristic",
                facts=[
                    f"Requested class: {DRUG_CATALOG.get(rx_ingredient, {}).get('therapeutic_class')}",
                    f"Recent dependence-associated exposures: {prior_dependence_exposure}",
                ],
                mechanism="Repeated sedative exposure can increase dependence/withdrawal risk",
                action="Use shortest duration, monitor closely, and consider non-dependence-forming alternatives.",
                uncertainty="No refill/multiple prescriber history in demo dataset.",
            )
        )

    if not findings:
        findings.append(
            _mk_finding(
                category="overall",
                title="No high-severity rule match in seeded dataset",
                level=RiskLevel.LOW,
                confidence=0.63,
                evidence="Rule engine fallback",
                facts=["No critical conflicts found in current seeded rules"],
                mechanism="Rule set did not identify major contraindication",
                action="Proceed only with routine clinician review and monitoring.",
                uncertainty="Seed knowledge base is limited and non-exhaustive.",
            )
        )

    findings.sort(key=lambda f: RISK_ORDER[f.risk_level], reverse=True)

    # risk-priority de-dup for categories
    best_by_category: dict[str, RiskFinding] = {}
    for finding in findings:
        previous = best_by_category.get(finding.category)
        if previous is None or RISK_ORDER[finding.risk_level] > RISK_ORDER[previous.risk_level]:
            best_by_category[finding.category] = finding

    return sorted(best_by_category.values(), key=lambda f: RISK_ORDER[f.risk_level], reverse=True)


def highest_risk(findings: list[RiskFinding]) -> RiskLevel:
    if not findings:
        return RiskLevel.LOW
    return max(findings, key=lambda f: RISK_ORDER[f.risk_level]).risk_level


def relationship_map(patient: PatientProfile, prescription: PrescriptionInput, findings: list[RiskFinding]) -> dict:
    nodes = [
        {"id": "patient", "label": patient.name, "type": "patient"},
        {"id": "rx", "label": prescription.drug_name, "type": "proposed_rx"},
    ]
    edges = []
    for dx in patient.diagnoses:
        node_id = f"dx:{dx}"
        nodes.append({"id": node_id, "label": dx, "type": "diagnosis"})
        edges.append({"from": "patient", "to": node_id, "label": "has diagnosis"})

    for med in patient.current_medications + patient.recently_stopped_medications:
        node_id = f"med:{med.ingredient}"
        nodes.append({"id": node_id, "label": med.drug_name, "type": "medication"})
        edges.append({"from": "patient", "to": node_id, "label": "exposed"})

    for finding in findings:
        node_id = f"risk:{finding.category}"
        nodes.append({"id": node_id, "label": finding.risk_level.value, "type": "risk"})
        edges.append({"from": "rx", "to": node_id, "label": finding.category})

    # remove duplicates by id
    unique_nodes = {n["id"]: n for n in nodes}
    return {"nodes": list(unique_nodes.values()), "edges": edges}
