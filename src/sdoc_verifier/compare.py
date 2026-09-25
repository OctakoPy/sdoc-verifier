"""Deterministic comparison of the seven canonical shipment fields."""

from __future__ import annotations

import re

from sdoc_verifier.models import FIELDS, ComparisonResult, ExtractedFields

_WS_RE = re.compile(r"\s+")
_COUNT_PAIR_RE = re.compile(r"(\d+)\s*[xX]\s*([A-Za-z0-9']{2,})")
_PORT_CODE_RE = re.compile(r"\(([A-Z]{5})\)")
_BARE_CODE_RE = re.compile(r"^[A-Z]{5}$")
_TEXT_FIELDS = frozenset(
    {"shipper", "consignee", "notify_party", "port_of_loading", "port_of_discharge"}
)


def _normalize_text(value: str) -> str:
    folded = value.replace("|", ";")
    folded = _WS_RE.sub(" ", folded).strip().upper()
    segments = [segment.strip() for segment in folded.split(";")]
    return "; ".join(segment for segment in segments if segment)


def _digits_only(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    return str(int(digits)) if digits else ""


def _normalize_count(value: str) -> str:
    pairs = _COUNT_PAIR_RE.findall(value)
    if pairs:
        return ";".join(
            sorted(
                f"{int(count)}X{kind.upper().replace(chr(39), '')}"
                for count, kind in pairs
            )
        )
    return _digits_only(value)


def normalize_value(field: str, value: str) -> str:
    """Normalize a value according to its canonical field type."""
    if field == "container_count":
        return _normalize_count(value)
    if field == "gross_weight_kg":
        return _digits_only(value)
    return _normalize_text(value)


def _port_code_equivalent(first: str, second: str) -> bool:
    for bare, full in ((first, second), (second, first)):
        if _BARE_CODE_RE.fullmatch(bare) and _PORT_CODE_RE.search(full):
            return True
    return False


def values_match(field: str, si_value: str, bl_value: str) -> bool:
    """Compare one pair after normalization; blank values are handled by review."""
    if not si_value.strip() or not bl_value.strip():
        return True
    normalized_si = normalize_value(field, si_value)
    normalized_bl = normalize_value(field, bl_value)
    if normalized_si == normalized_bl:
        return True
    if field in ("port_of_loading", "port_of_discharge"):
        return _port_code_equivalent(normalized_si, normalized_bl)
    return False


def compare_fields(
    si_fields: ExtractedFields, bl_fields: ExtractedFields
) -> ComparisonResult:
    """Compare SI values against draft BL values in canonical field order."""
    field_matches: dict[str, bool] = {}
    values: dict[str, tuple[str, str]] = {}
    for name in FIELDS:
        si_value = getattr(si_fields, name)
        bl_value = getattr(bl_fields, name)
        field_matches[name] = values_match(name, si_value, bl_value)
        values[name] = (si_value, bl_value)
    return ComparisonResult(field_matches=field_matches, values=values)


__all__ = ["compare_fields", "normalize_value", "values_match"]
