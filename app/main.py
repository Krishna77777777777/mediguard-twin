from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data import (
    DEMO_PATIENTS,
    DISCLAIMER,
    EVIDENCE_SOURCES,
    KNOWLEDGE_BASE_VERSION,
    PROVIDER_ADAPTERS,
)
from .models import AnalysisResult, PatientProfile, PrescriptionInput, SandboxRequest
from .services.safety import highest_risk, relationship_map, analyze_risks
from .services.sandbox import run_sandbox
from .services.timeline import timeline_for_30_days

app = FastAPI(
    title="MediGuard Twin",
    version="0.1.0",
    description="Explainable medication-safety decision-support prototype. Not medical advice.",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "mediguard-twin",
        "knowledge_base_version": KNOWLEDGE_BASE_VERSION,
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/patients")
def list_patients() -> list[dict]:
    return [{"id": p.id, "name": p.name, "age": p.age, "diagnoses": p.diagnoses} for p in DEMO_PATIENTS.values()]


@app.get("/api/patients/{patient_id}", response_model=PatientProfile)
def get_patient(patient_id: str) -> PatientProfile:
    patient = DEMO_PATIENTS.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(patient: PatientProfile, prescription: PrescriptionInput) -> AnalysisResult:
    timeline = timeline_for_30_days(
        patient.current_medications,
        patient.recently_stopped_medications,
        prescription,
    )
    findings = analyze_risks(patient, prescription, timeline)
    return AnalysisResult(
        patient_id=patient.id,
        prescription=prescription,
        timeline=timeline,
        findings=findings,
        highest_risk=highest_risk(findings),
        disclaimer=DISCLAIMER,
    )


@app.post("/api/analyze/demo/{patient_id}", response_model=AnalysisResult)
def analyze_demo(patient_id: str, prescription: PrescriptionInput) -> AnalysisResult:
    patient = DEMO_PATIENTS.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return analyze(patient=patient, prescription=prescription)


@app.post("/api/sandbox", response_model=dict)
def sandbox(payload: SandboxRequest) -> dict:
    simulation = run_sandbox(payload.patient, payload.prescription)
    timeline = timeline_for_30_days(
        payload.patient.current_medications,
        payload.patient.recently_stopped_medications,
        payload.prescription,
    )
    findings = analyze_risks(payload.patient, payload.prescription, timeline)
    return {
        "simulation": simulation,
        "relationship_map": relationship_map(payload.patient, payload.prescription, findings),
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/meta")
def meta() -> dict:
    return {
        "disclaimer": DISCLAIMER,
        "evidence_sources": EVIDENCE_SOURCES,
        "provider_adapters": PROVIDER_ADAPTERS,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
