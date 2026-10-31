"""Compatibility entry point, now using local Gemma instead of Gemini."""

import json

from local_llm import chat_json, model_name


def ask_gemini(treatment: str, summary: str, retries: int = 3) -> str:
    evidence = json.loads(summary).get("evidence", [])
    if not evidence:
        raise ValueError("The retrieved abstracts do not contain verified tumor-volume measurements for this treatment. Try a more specific treatment; no clinical effect was invented.")
    schema = {
        "type": "object", "properties": {
            "evidence_index": {"type": "integer", "minimum": 0, "maximum": len(evidence) - 1},
        }, "required": ["evidence_index"], "additionalProperties": False,
    }
    selected = chat_json(
        "For an educational visualization of " + treatment + ", select ONE relevant "
        "observed brain-tumor volume decrease from the verified evidence array below. "
        "Return its zero-based evidence_index. Do not extrapolate, average, or predict "
        "a patient's response. For paired_volumes, Python has already calculated the "
        "percentage from the reported baseline and follow-up volumes.\n\n" + summary,
        schema,
    )
    index = selected.get("evidence_index") if isinstance(selected, dict) else None
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(evidence):
        raise ValueError("Local model selected an invalid evidence observation.")
    match = evidence[index]
    result = {
        "reduction": match["reduction_percent"] / 100,
        "source_id": match["source_id"], "evidence_quote": match["quote"],
        "evidence_type": match["evidence_type"], "model": model_name(),
        "notice": "Educational illustration of a reported study observation; not a patient-specific treatment prediction.",
    }
    for key in ("baseline_volume", "followup_volume", "units", "calculation"):
        if key in match:
            result[key] = match[key]
    return json.dumps(result)
