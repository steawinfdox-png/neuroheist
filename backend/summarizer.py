"""Extract traceable tumor-volume observations with the local Gemma model."""

import json
import math
import re

from local_llm import chat_json


_NUMBER = r"(?:\d+(?:\.\d+)?|\.\d+)"
_UNIT = r"(?:cc|cm\s*(?:\^\s*3|3|³)|mm\s*(?:\^\s*3|3|³)|ml)"
_SPREAD = rf"(?:\s*(?:±|\+\s*/\s*-|\+/-)\s*{_NUMBER})?"
_PAIR = re.compile(
    rf"\bfrom\s+(?P<baseline>{_NUMBER}){_SPREAD}\s*(?P<unit1>{_UNIT})?"
    rf"\s*(?:\([^)]{{0,80}}\)\s*)?to\s+(?P<followup>{_NUMBER}){_SPREAD}"
    rf"\s*(?P<unit2>{_UNIT})?\b", re.I,
)


def _normalized(text):
    return " ".join(text.casefold().split())


def _unit(text):
    value = re.sub(r"[\s^]", "", text.casefold()).replace("³", "3")
    return {"cc": "cm3", "ml": "cm3"}.get(value, value)


def _finite_number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _tumor_volume_quote(quote):
    # An excerpt must identify the measured tumor/lesion volume. A whole paper
    # can discuss edema too, but its edema measurements cannot drive a scenario.
    if re.search(r"\bedema\b|\boedema\b|\bAVM\b|arteriovenous|healthy|normal brain", quote, re.I):
        return False
    if re.search(r"defined|definition|criteria|criterion|threshold|response rate|survival", quote, re.I):
        return False
    target = r"(?:tumou?rs?|metasta(?:sis|ses|tic)|lesions?|gliomas?|glioblastomas?|meningiomas?|schwannomas?)"
    return bool(
        re.search(rf"\b{target}\b[^.;]{{0,65}}\bvolum", quote, re.I)
        or re.search(rf"\bvolum[^.;]{{0,65}}\b{target}\b", quote, re.I)
    ) and bool(re.search(r"reduc|decreas|shrink|regress", quote, re.I))


def _paired_observation(item, quote):
    baseline, followup = item.get("baseline_volume"), item.get("followup_volume")
    units = item.get("units")
    if not _finite_number(baseline) or not _finite_number(followup) or not isinstance(units, str):
        return None
    if baseline <= 0 or not 0 <= followup <= baseline:
        return None
    for pair in _PAIR.finditer(quote):
        if abs(float(pair["baseline"]) - baseline) > 0.000001 or abs(float(pair["followup"]) - followup) > 0.000001:
            continue
        first_unit, second_unit = pair["unit1"], pair["unit2"]
        if not first_unit and not second_unit:
            continue
        first_unit = _unit(first_unit or second_unit)
        second_unit = _unit(second_unit or pair["unit1"])
        if first_unit != second_unit or _unit(units) != first_unit:
            continue
        # Calculate only from paired reported volumes, never from a patient
        # response rate, diameter, standard deviation, or a model-made number.
        percent = (baseline - followup) / baseline * 100
        return {
            "evidence_type": "paired_volumes", "reduction_percent": percent,
            "baseline_volume": float(baseline), "followup_volume": float(followup),
            "units": first_unit,
            "calculation": "(reported baseline volume - reported follow-up volume) / reported baseline volume",
        }
    return None


def summarize(content: str):
    schema = {
        "type": "object", "properties": {"evidence": {"type": "array", "maxItems": 3, "items": {
            "type": "object", "properties": {
                "source_id": {"type": "string"}, "quote": {"type": "string"},
                "evidence_type": {"type": "string", "enum": ["percentage", "paired_volumes"]},
                "reduction_percent": {"type": ["number", "null"]},
                "baseline_volume": {"type": ["number", "null"]},
                "followup_volume": {"type": ["number", "null"]},
                "units": {"type": ["string", "null"]},
            }, "required": ["source_id", "quote", "evidence_type", "reduction_percent", "baseline_volume", "followup_volume", "units"],
            "additionalProperties": False,
        }}}, "required": ["evidence"], "additionalProperties": False,
    }
    result = chat_json(
        "Extract at most three OBSERVED decreases in BRAIN TUMOR, metastasis, or neoplastic "
        "lesion VOLUME after treatment from the excerpts below. Two evidence types are allowed:\n"
        "percentage: an explicitly reported percentage decrease in tumor volume; copy that "
        "number into reduction_percent and leave baseline_volume, followup_volume, units null.\n"
        "paired_volumes: tumor volume explicitly decreased FROM a positive baseline TO a "
        "follow-up volume, both in the SAME cubic-volume units. Copy the central baseline and "
        "follow-up values into baseline_volume/followup_volume; ignore plus-minus standard "
        "deviations. Copy units (cc, cm3, ml or mm3); leave reduction_percent null. Python "
        "will calculate the percent. Example: metastasis volume decreased from 3.79±4.12 cc "
        "to 2.8±4.48 cc means baseline_volume=3.79, followup_volume=2.8, units=cc.\n"
        "quote must be an EXACT contiguous source excerpt identifying tumor/metastasis/lesion "
        "volume, the observed decrease, and the relevant numbers. Use exact source_id. "
        "Exclude edema, healthy brain, arteriovenous malformations, survival, response rates, "
        "response-definition thresholds, dose, diameter, and percentages of patients. "
        "Never invent values. Zero decrease is allowed. Return {\"evidence\": []} if neither "
        "type is supported.\n\n" + content,
        schema,
    )
    if not isinstance(result, dict) or not isinstance(result.get("evidence"), list):
        raise ValueError("Local model returned invalid evidence.")
    sources = content.split("\n\n--- NEXT SOURCE ---\n\n")
    valid = []
    for item in result["evidence"][:3]:
        if not isinstance(item, dict):
            continue
        quote, source_id = item.get("quote", ""), item.get("source_id", "")
        if not isinstance(quote, str) or not isinstance(source_id, str) or not source_id:
            continue
        matching = [source for source in sources if source.startswith("Source: " + source_id + "\n")]
        if not matching or not quote or _normalized(quote) not in _normalized(matching[0]) or not _tumor_volume_quote(quote):
            continue
        kind = item.get("evidence_type", "percentage")
        if kind not in {"percentage", "paired_volumes"}:
            continue
        if kind == "paired_volumes":
            observation = _paired_observation(item, quote)
            if observation is None:
                continue
        else:
            value = item.get("reduction_percent")
            if not _finite_number(value) or not 0 <= value <= 100:
                continue
            numbers = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|percent\b)", quote, re.I)
            if not any(abs(float(number) - value) < 0.000001 for number in numbers):
                continue
            observation = {"evidence_type": "percentage", "reduction_percent": float(value)}
        valid.append({"source_id": source_id, "quote": quote, **observation})
    return json.dumps({"evidence": valid})
