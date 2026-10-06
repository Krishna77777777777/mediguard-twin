from datetime import date, timedelta

from app.models import Frequency, MedicationRecord, PrescriptionInput
from app.services.timeline import timeline_for_30_days


def test_timeline_overlap_and_recent_exposure():
    today = date.today()
    med = MedicationRecord(
        drug_name="Diazepam",
        ingredient="diazepam",
        therapeutic_class="benzodiazepine",
        dose=5,
        unit="mg",
        route="oral",
        frequency=Frequency.BID,
        start_date=today - timedelta(days=10),
        duration_days=5,
    )
    rx = PrescriptionInput(
        drug_name="Lorazepam",
        ingredient="lorazepam",
        strength="1 mg",
        dose=1,
        unit="mg",
        route="oral",
        frequency=Frequency.DAILY,
        start_date=today - timedelta(days=8),
        duration_days=7,
        indication="anxiety",
    )

    timeline = timeline_for_30_days([], [med], rx, today=today)
    assert len(timeline) == 1
    assert timeline[0].recently_stopped is True
    assert timeline[0].overlap_with_new_rx_days >= 1
    assert timeline[0].days_since_last_dose is not None
