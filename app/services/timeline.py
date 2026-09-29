from __future__ import annotations

from datetime import date, timedelta

from ..models import MedicationRecord, PrescriptionInput, TimelineEntry


def medication_stop_date(med: MedicationRecord) -> date:
    return med.start_date + timedelta(days=med.duration_days - 1)


def timeline_for_30_days(
    current_meds: list[MedicationRecord],
    stopped_meds: list[MedicationRecord],
    prescription: PrescriptionInput,
    today: date | None = None,
) -> list[TimelineEntry]:
    today = today or date.today()
    lookback = today - timedelta(days=30)
    rx_stop = prescription.start_date + timedelta(days=prescription.duration_days - 1)

    entries: list[TimelineEntry] = []
    for med in [*current_meds, *stopped_meds]:
        stop_date = medication_stop_date(med)
        if stop_date < lookback and med.start_date < lookback:
            continue

        overlap = max(
            0,
            (
                min(stop_date, rx_stop)
                - max(med.start_date, prescription.start_date)
            ).days
            + 1,
        )
        active_now = med.start_date <= today <= stop_date
        recently_stopped = stop_date < today and (today - stop_date).days <= 30
        days_since_last = (today - stop_date).days if stop_date < today else None

        entries.append(
            TimelineEntry(
                drug_name=med.drug_name,
                ingredient=med.ingredient,
                therapeutic_class=med.therapeutic_class,
                start_date=med.start_date,
                stop_date=stop_date,
                currently_active=active_now,
                recently_stopped=recently_stopped,
                days_since_last_dose=days_since_last,
                recent_exposure=(today - stop_date).days <= 30,
                overlap_with_new_rx_days=overlap,
            )
        )

    entries.sort(key=lambda x: x.start_date)
    return entries
