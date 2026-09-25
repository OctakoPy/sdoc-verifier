"""Deterministic language routing for optional label translation.

The router identifies documents whose labels need an explicit translation
step. It is pure and does not call a model. English labels with inline
annotations remain on the deterministic path.
"""

from __future__ import annotations

import re
from typing import Literal

__all__ = ["Language", "detect_document_language"]

#: Languages the router distinguishes; ``"en"`` keeps the deterministic path.
Language = Literal["en", "zh", "bm"]

#: CJK unified ideographs (plus extension A) — the extract stage already
#: strips exactly this range from labels (canonical label normalization).
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

#: Row counts as a native-ZH label row when its first non-space character is
#: CJK (title rows included).
#: Distinctive BM shipping markers for the optional translation path.
#: are matched on the casefolded text; every marker is deliberately specific
#: to BM document language so English sample documents cannot accumulate the
#: threshold of two distinct markers.
_BM_MARKERS: tuple[str, ...] = (
    "arahan penghantaran",
    "draf bill of lading",
    "bill of lading (draf)",
    "penghantar",
    "penerima",
    "pemberitahu",
    "pelabuhan pemuatan",
    "pelabuhan bongkar",
    "jumlah kontena",
    "berat kasar",
    "sila semak",
    "sila dapati",
    "terlampir",
    "percanggahan",
)

#: Distinct-marker threshold for the BM classification.
_BM_MARKER_THRESHOLD = 2

#: CJK-first rows required to classify a document native-ZH.
_ZH_ROW_THRESHOLD = 2


def _cjk_first_rows(text: str) -> int:
    """Count rows whose first non-space character is a CJK ideograph.

    Example:
        >>> _cjk_first_rows("SHIPPER: A\\n\\u53d1\\u8d27\\u4eba: B")
        1
    """
    count = 0
    for row in text.splitlines():
        stripped = row.lstrip()
        if stripped and _CJK_RE.match(stripped[0]):
            count += 1
    return count


def _distinct_bm_markers(text: str) -> int:
    """Count distinct BM markers present in the casefolded text.

    Example:
        >>> _distinct_bm_markers("Sila semak draf Bill of Lading") >= 2
        True
    """
    casefolded = text.casefold()
    return sum(1 for marker in _BM_MARKERS if marker in casefolded)


def detect_document_language(text: str) -> Language:
    """Classify one parsed document's language: ``"zh"``, ``"bm"`` or ``"en"``.

    Pure and deterministic: same text, same answer, no network. ``"en"`` is
    the default — annotation-level bilingual documents (English labels with
    CJK glosses) and all existing sample
    documents keep the fully deterministic path.

    Args:
        text: The parsed document's full text (title, labels, values).

    Returns:
        The detected language tag.

    Example:
        >>> detect_document_language(
        ...     "Arahan Penghantaran\\nPenghantar: ACME\\nPenerima: ORBIS"
        ... )
        'bm'
        >>> detect_document_language("SHIPPING INSTRUCTION\\nShipper: ACME")
        'en'
    """
    if _cjk_first_rows(text) >= _ZH_ROW_THRESHOLD:
        return "zh"
    if _distinct_bm_markers(text) >= _BM_MARKER_THRESHOLD:
        return "bm"
    return "en"
