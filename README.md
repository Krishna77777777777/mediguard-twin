# MediGuard Twin

> **Safety notice**: MediGuard Twin is a clinical decision-support **prototype** for medication-safety triage. It is **not medical advice**, does **not** replace licensed clinician judgment, and must not independently make prescribing decisions.

MediGuard Twin is a full-stack hackathon MVP for explainable medication safety with:
- patient profile analysis,
- prescription risk analysis,
- 30-day medication timeline,
- deterministic virtual-patient sandbox,
- evidence-aware risk cards and relationship map.

## Architecture

```text
FastAPI backend (Python 3.11+)
├── Typed domain models (Pydantic)
├── Seeded medication knowledge base
├── Safety engine (rule-driven, explainable)
├── 30-day timeline engine
├── Virtual sandbox simulator with stop cases
└── Static dashboard UI served by FastAPI
```

### Key modules
- `/home/runner/work/mediguard-twin/mediguard-twin/app/main.py` – API routes + dashboard serving
- `/home/runner/work/mediguard-twin/mediguard-twin/app/models.py` – typed models
- `/home/runner/work/mediguard-twin/mediguard-twin/app/data.py` – synthetic demo patients + seeded knowledge base
- `/home/runner/work/mediguard-twin/mediguard-twin/app/services/timeline.py` – 30-day timeline logic
- `/home/runner/work/mediguard-twin/mediguard-twin/app/services/safety.py` – explainable safety rules + risk prioritization
- `/home/runner/work/mediguard-twin/mediguard-twin/app/services/sandbox.py` – counterfactual simulation + stop cases
- `/home/runner/work/mediguard-twin/mediguard-twin/app/services/adapters.py` – provider adapter interface contract
- `/home/runner/work/mediguard-twin/mediguard-twin/app/static/index.html` – polished responsive dashboard

## Features mapped to problem statement

1. **Patient profile**: age, weight, allergies, diagnoses, renal/liver indicators, pregnancy status, current/recent meds, adverse reactions.
2. **Prescription analyzer**: drug name, ingredient, strength, dose, unit, route, frequency, start date, duration, indication.
3. **30-day timeline**: active + recently stopped meds, overlap windows, recent exposure, days-since-last-dose, linked reaction events.
4. **Safety engine detections**:
   - drug-drug interactions,
   - drug-disease interactions,
   - duplicate ingredient and therapeutic-class duplication,
   - dose/frequency concerns,
   - allergy and cross-reactivity,
   - recent residual/overlap concerns,
   - dependence/misuse/withdrawal-risk flags.
5. **Evidence-aware outputs**: LOW/MODERATE/HIGH/CRITICAL + confidence, evidence source, patient facts, mechanism, clinician action, uncertainty notes.
6. **Virtual-patient sandbox**: deterministic short-horizon simulation with explicit stop cases.
7. **Dashboard**: patient overview, analyzer, timeline, risk cards, relationship map, sandbox controls/results, audit/evidence notes.
8. **Synthetic demo scenarios**:
   - `high-risk-renal` (renal + anticoagulant + sedative history)
   - `lower-risk`
9. **International data design**: local seeded KB + documented provider adapter interface for future integration.
10. **API docs and health endpoint**: `/docs`, `/openapi.json`, `/api/health`.
11. **Tests**: core safety rules, timeline calculations, risk prioritization, API smoke.
12. **Dockerized run path**: Dockerfile + docker-compose.

## Stop cases used in sandbox

Simulation can stop on high-risk trigger mapping for:
- anaphylaxis/allergy conflict,
- major bleeding,
- respiratory/CNS depression,
- QT/arrhythmia risk,
- renal/hepatic accumulation,
- overdose/dose concern,
- duplicate therapy,
- high dependence risk.

> Sandbox outputs are deterministic decision-support simulation events, **not biological guarantees**.

## Quick start

### Local Python run

```bash
cd /home/runner/work/mediguard-twin/mediguard-twin
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000`

### Docker Compose run

```bash
cd /home/runner/work/mediguard-twin/mediguard-twin
docker compose up --build
```

Open: `http://127.0.0.1:8000`

## API surface

- `GET /api/health` – service health + disclaimer + KB version
- `GET /api/meta` – evidence/provenance and provider-adapter metadata
- `GET /api/patients` – demo patient list
- `GET /api/patients/{patient_id}` – full patient profile
- `POST /api/analyze` – analyze user-provided patient + prescription
- `POST /api/analyze/demo/{patient_id}` – analyze against demo patient
- `POST /api/sandbox` – simulation + relationship map

### API docs
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

## Demo walkthrough

1. Start app and open dashboard.
2. Select `high-risk-renal`.
3. Enter `Ibuprofen / ibuprofen`, dose `400 mg`, frequency `tid`, duration `5`.
4. Run **Safety Analysis**.
5. Review CRITICAL/HIGH findings, confidence, evidence, and uncertainty.
6. Inspect 30-day timeline overlap + reaction events.
7. Run **Sandbox Simulation** and review stop cases + relationship map.
8. Repeat with `lower-risk` using low-dose acetaminophen for contrast.

## Knowledge base and provenance strategy

This MVP ships with a concise seeded demo knowledge base for offline reproducibility and no external API dependency.

Planned adapter integrations (interface in `app/services/adapters.py`):
- **RxNorm/RxNav** for normalized ingredients and concepts,
- **WHO ATC/DDD** for global class/DDD context,
- **FDA openFDA / DailyMed** for label warnings and references,
- **EMA** data for EEA products and product information.

The seed data is intentionally limited and **not exhaustive**.

## Testing

```bash
cd /home/runner/work/mediguard-twin/mediguard-twin
pytest -q
```

## Limitations

- Seeded demo data is intentionally small; production safety coverage requires expanded, clinically governed knowledge bases.
- No live EHR/FHIR ingestion in this MVP.
- Dose logic is rule-based and simplified (unit harmonization and specialty dosing are limited).
- Dependence risk is heuristic and not a diagnosis.
- Not validated for clinical deployment.

## Future roadmap

- FHIR R4 ingestion pipeline (MedicationRequest, Condition, AllergyIntolerance, Observation).
- Expanded interaction graph and conflict ontology.
- Stronger international localization and multilingual warning summaries.
- Reviewer override workflow and longitudinal audit persistence.
- PostgreSQL persistence layer (repository/service abstraction already suitable for extension).
- Governance tools for rule authoring, evidence versioning, and reviewer sign-off.
