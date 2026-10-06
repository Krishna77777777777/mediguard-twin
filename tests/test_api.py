from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_meta_endpoints():
    health = client.get('/api/health')
    assert health.status_code == 200
    assert health.json()['status'] == 'ok'

    meta = client.get('/api/meta')
    assert meta.status_code == 200
    assert '/docs' in meta.json()['docs']


def test_demo_analysis_smoke():
    payload = {
        'drug_name': 'Ibuprofen',
        'ingredient': 'ibuprofen',
        'strength': '400 mg',
        'dose': 400,
        'unit': 'mg',
        'route': 'oral',
        'frequency': 'bid',
        'start_date': date.today().isoformat(),
        'duration_days': 5,
        'indication': 'pain',
    }
    res = client.post('/api/analyze/demo/high-risk-renal', json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data['findings']
    assert data['highest_risk'] in {'HIGH', 'CRITICAL'}


def test_sandbox_smoke():
    patient = client.get('/api/patients/high-risk-renal').json()
    payload = {
        'patient': patient,
        'prescription': {
            'drug_name': 'Ibuprofen',
            'ingredient': 'ibuprofen',
            'strength': '400 mg',
            'dose': 400,
            'unit': 'mg',
            'route': 'oral',
            'frequency': 'bid',
            'start_date': date.today().isoformat(),
            'duration_days': 5,
            'indication': 'pain',
        }
    }
    res = client.post('/api/sandbox', json=payload)
    assert res.status_code == 200
    data = res.json()
    assert 'simulation' in data
    assert 'relationship_map' in data
