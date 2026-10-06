from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class NormalizedMedication:
    input_name: str
    generic_name: str
    therapeutic_class: str
    source: str


class MedicationDataProvider(Protocol):
    name: str

    def normalize_medication(self, raw_name: str) -> NormalizedMedication:
        """Resolve medication names to normalized generic + class terms."""

    def get_evidence_reference(self, ingredient: str) -> list[str]:
        """Return evidence references/citations for the ingredient or class."""
