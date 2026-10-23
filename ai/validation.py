"""Schema and reference validation for generated output."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from .schemas import ManagerBriefing, ShipmentExplanation


@dataclass
class ValidationOutcome:
    output: Any = None
    errors: list = field(default_factory=list)

    @property
    def ok(self):
        return self.output is not None and not self.errors


def _parse(text, model):
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return model.model_validate(json.loads(cleaned)), []
    except json.JSONDecodeError as exc:
        return None, [f"response is not valid JSON ({exc.msg})"]
    except ValidationError as exc:
        return None, [f"{'.'.join(map(str, e['loc'])) or 'root'}: {e['msg']}" for e in exc.errors()[:10]]


def _unknown_ids(cited, evidence):
    return sorted(set(cited) - evidence.ids)


def validate_explanation(text, evidence):
    out, errors = _parse(text, ShipmentExplanation)
    if out is None:
        return ValidationOutcome(errors=errors)
    if out.shipment_id != evidence.subject:
        errors.append(f"shipment_id {out.shipment_id} does not match the requested shipment {evidence.subject}")
    rules = set(evidence.deterministic["rules"])
    if out.issue_category == "none" and rules:
        errors.append("issue_category is 'none' but the rules flagged this shipment")
    elif out.issue_category != "none" and out.issue_category not in rules:
        errors.append(f"issue_category {out.issue_category!r} is not one of the flagged rules {sorted(rules)}")
    cited = [i for s in out.observed_facts for i in s.evidence_ids]
    cited += out.recommended_next_action.evidence_ids
    cited += [i for c in out.conflicts for i in c.evidence_ids]
    unknown = _unknown_ids(cited, evidence)
    if unknown:
        errors.append(f"cites IDs that are not in the evidence: {', '.join(unknown)}")
    if out.conflicts and not out.requires_review:
        errors.append("conflicts are reported but requires_review is false")
    return ValidationOutcome(output=None if errors else out, errors=errors)


def validate_briefing(text, evidence):
    out, errors = _parse(text, ManagerBriefing)
    if out is None:
        return ValidationOutcome(errors=errors)
    det = evidence.deterministic
    if out.shipment_count != det["shipment_count"]:
        errors.append(f"shipment_count {out.shipment_count} does not match the rules ({det['shipment_count']})")
    if out.exception_count != det["exception_count"]:
        errors.append(f"exception_count {out.exception_count} does not match the rules ({det['exception_count']})")
    flagged = {f["shipment_id"] for f in evidence.flags}
    listed = {i.shipment_id for i in out.items}
    if listed - flagged:
        errors.append(f"lists shipments that are not flagged: {', '.join(sorted(listed - flagged))}")
    if flagged - listed:
        errors.append(f"omits flagged shipments: {', '.join(sorted(flagged - listed))}")
    unknown = _unknown_ids([i for item in out.items for i in item.evidence_ids], evidence)
    if unknown:
        errors.append(f"cites IDs that are not in the evidence: {', '.join(unknown)}")
    return ValidationOutcome(output=None if errors else out, errors=errors)
