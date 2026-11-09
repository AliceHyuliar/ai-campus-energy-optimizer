"""Provider-independent preparation only. No provider is configured or called."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from backend.app.analysis import AnalysisReport


class ExplanationProvider(Protocol):
    def explain(self, analysis: "AnalysisReport") -> str:
        """Explain immutable structured estimates; never decide or control equipment."""
        ...


def disconnected_ai() -> dict:
    # Explanations and internal rationales are never passed off as Gemini output.
    return {"status": "not_connected", "explanation": None}
