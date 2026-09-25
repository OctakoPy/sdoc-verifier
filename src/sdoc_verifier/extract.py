"""Anchored field extraction from normalized parser rows.

:func:`normalize_label` removes presentation noise and :data:`SYNONYM_MAP`
maps the resulting labels to the seven canonical fields. The anchored
variant reports the source-row indices that produced every value. Missing
fields remain blank so the review stage can request manual review.

Both colon rows and bare-label blocks are supported. Table headers and
known non-field labels terminate a bare-label block without becoming values.
"""

from __future__ import annotations

import re

from sdoc_verifier.models import ExtractedFields, ParsedDocument

__all__ = [
    "SYNONYM_MAP",
    "assign_roles",
    "extract_fields",
    "extract_fields_anchored",
    "field_for_label",
    "normalize_label",
]

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]+")
_TRAILING_COLONS_RE = re.compile(r"[:\uff1a]+\s*$")
_PARENS_RE = re.compile(r"\([^()]*\)")
_WS_RE = re.compile(r"\s+")

#: Placeholder markers that mean "value intentionally not specified".
#: They are presentation, not data — extraction blanks them so the review
#: stage escalates ``missing_value`` (review policy rule 4).
_PLACEHOLDER_RE = re.compile(
    r"^(?:\?{1,}|_+|-{1,}|TBC|TBA|TBD|N/?A|NONE)[\s.?_-]*$", re.IGNORECASE
)

#: Bare pdf table headers that must NOT start a field block: under them sit
#: per-container rows, not values for the header's own field.
_TABLE_HEADERS = ("CONTAINER NO", "DESCRIPTION", "GROSS WEIGHT")

#: Known NON-field labels (normalized). They end a bare-label block just
#: like mapped labels do — e.g. the glued pdf line
#: ``Export Carrier (vessel, voyage)SOLID 16 V.044NW2`` must not be
#: swallowed into the preceding port value.
_NON_FIELD_LABELS = frozenset(
    {
        "BOOKING NO",
        "BOOKING REF",
        "BOOKING REFERENCE",
        "B/L NUMBER",
        "B/L NO",
        "BL NO",
        "BILL OF LADING NO",
        "VESSEL",
        "OCEAN VESSEL",
        "EXPORT CARRIER",
        "VOY",
        "VOY.",
        "VOYAGE",
        "VOYAGE NO",
        "FREIGHT",
        "HS CODE",
        "DESCRIPTION",
        "DESCRIPTION OF GOODS",
        "COMMODITY",
        "KINDS OF PACKAGES; DESCRIPTION OF GOODS",
        "ORDER NO",
        "OC NO",
        "TEL",
        "P.O. BOX",
        "NEW NO",
        "NET WEIGHT",
        "BL INSTRUCTION",
        "BILL OF LADING",
    }
)


def normalize_label(label: str) -> str:
    """Reduce a surface label to its canonical comparison form.

    Order matters: strip whitespace and trailing colons, remove CJK
    annotation characters (``发货人`` etc. — inline or parenthesised), then
    drop **all** parenthetical segments: units (``(KG)``), port codes
    (``(POL)``), qualifiers (``(Non-Negotiable)``) and leftover empty
    ``()`` are presentation noise, and stripping them keeps the map small
    and collision-free. Finally uppercase and collapse whitespace.

    Args:
        label: The raw label text, e.g. ``"Shipper (发货人):"``.

    Returns:
        The normalized label, e.g. ``"SHIPPER"``.

    Example:
        >>> normalize_label("  Shipper (发货人): ")
        'SHIPPER'
        >>> normalize_label("Port of Loading (POL)")
        'PORT OF LOADING'
        >>> normalize_label("Gross Weight毛重(KGS)")
        'GROSS WEIGHT'
        >>> normalize_label("NOTIFY PARTY")
        'NOTIFY PARTY'
    """
    cleaned = label.strip()
    cleaned = _TRAILING_COLONS_RE.sub("", cleaned)
    cleaned = _CJK_RE.sub("", cleaned)
    cleaned = _PARENS_RE.sub("", cleaned)
    cleaned = _WS_RE.sub(" ", cleaned).strip()
    return cleaned.upper()


#: Normalized surface label -> canonical field key (``models.FIELDS``).
#: Keys are exactly :func:`normalize_label` outputs for every known surface
#: form; unmapped labels (B/L numbers, booking refs, vessel names, freight
#: terms, HS codes, cargo descriptions, address fragments) are
#: intentionally absent — extraction ignores them.
SYNONYM_MAP: dict[str, str] = {
    # shipper
    "SHIPPER": "shipper",
    "SHIPPER/EXPORTER": "shipper",
    # consignee
    "CONSIGNEE": "consignee",
    "TO THE ORDER OF": "consignee",
    # notify party
    "NOTIFY PARTY": "notify_party",
    "NOTIFY": "notify_party",
    "NOTIFY PARTY/INTERMEDIATE CONSIGNEE": "notify_party",
    # port of loading
    "PORT OF LOADING": "port_of_loading",
    "LOAD PORT": "port_of_loading",
    "POL": "port_of_loading",
    # port of discharge
    "PORT OF DISCHARGE": "port_of_discharge",
    "DISCHARGE PORT": "port_of_discharge",
    "POD": "port_of_discharge",
    # container count
    "NO. OF CONTAINERS": "container_count",
    "NUMBER OF CONTAINERS": "container_count",  # translated labels
    "TOTAL CONTAINERS": "container_count",
    "TOTAL NUMBER OF CONTAINERS": "container_count",  # translated labels
    "TOTAL CONTAINER": "container_count",  # translated labels
    "NO. OF CONTAINERS OR PACKAGES": "container_count",
    "CONTAINER COUNT": "container_count",
    "CONTAINER QUANTITY": "container_count",  # translated labels
    "CONTAINERS": "container_count",  # OCR transcriptions (optional OCR policy)
    # gross weight (parenthetical units stripped by normalization)
    "GROSS WEIGHT": "gross_weight_kg",
    "GROSS WT": "gross_weight_kg",
    "TOTAL GROSS WEIGHT": "gross_weight_kg",
    "TOTAL GROSS WT": "gross_weight_kg",
    "GROSS WEIGHTII": "gross_weight_kg",
    "TOTAL GROSS WEIGHTII": "gross_weight_kg",
}


def field_for_label(label: str) -> str | None:
    """Canonical field for a surface label, or ``None`` when unmapped.

    Example:
        >>> field_for_label("Notify Party/Intermediate Consignee (通知人)")
        'notify_party'
        >>> field_for_label("B/L NUMBER") is None
        True
        >>> field_for_label("Load Port")
        'port_of_loading'
    """
    normalized = normalize_label(label)
    return SYNONYM_MAP.get(normalized)


def _is_placeholder(value: str) -> bool:
    """True when a value is a placeholder marker, not data.

    Example:
        >>> _is_placeholder("N/A")
        True
        >>> _is_placeholder("TBA")
        True
        >>> _is_placeholder("131,058 KG")
        False
    """
    return bool(_PLACEHOLDER_RE.match(value.strip()))


def extract_fields_anchored(
    document: ParsedDocument,
) -> tuple[ExtractedFields, dict[str, list[int]]]:
    """Extract canonical fields and per-field row anchors.

    The single source of extraction truth: :func:`extract_fields` delegates
    here and drops the anchors. Walking logic is byte-for-byte the
    historical ``extract_fields`` body — only anchor bookkeeping was added,
    so values (and every downstream verdict) are unchanged.

    Args:
        document: A parser output (``rows`` carry ``Label: value`` strings
            and/or bare-label blocks; ``text`` backs bare pdf tables).

    Returns:
        ``(fields, anchors)`` where ``anchors`` maps each canonical field to
        the **0-based row indices** in ``document.rows`` that produced its
        value:

        - colon rows contribute their own row index;
        - bare-label blocks (pdf) contribute the label row plus every
          continuation row consumed into the value, as a contiguous range.

        Every canonical field key is present (empty list when the field was
        not found), so consumers can index without key checks. Anchors are
        for provenance/highlighting only — never re-parse them into values.

    Example:
        >>> doc = ParsedDocument(
        ...     path="attachments/a_SI.txt",
        ...     fmt="txt",
        ...     kind="SI",
        ...     text="Shipper: ACME\\nPOL: BUATAN",
        ...     rows=("Shipper: ACME", "POL: BUATAN"),
        ... )
        >>> fields, anchors = extract_fields_anchored(doc)
        >>> fields.shipper
        'ACME'
        >>> anchors["shipper"], anchors["port_of_loading"]
        ([0], [1])
        >>> anchors["consignee"]  # absent field -> present, empty
        []
    """
    values: dict[str, str] = {}
    anchors: dict[str, list[int]] = {
        name: [] for name in ExtractedFields.__dataclass_fields__
    }
    rows = document.rows
    index = 0
    while index < len(rows):
        row = rows[index]
        if ":" in row:
            label, _, value = row.partition(":")
            field = field_for_label(label)
            if field and not values.get(field):
                values[field] = "" if _is_placeholder(value) else value.strip()
                anchors[field].append(index)
            index += 1
            continue
        # Colon-less row: a bare label, a glued label+value line (pdf), a
        # table header, or noise. Longest-prefix matching tells them apart.
        norm_full = normalize_label(row)
        if norm_full in _TABLE_HEADERS or norm_full == "GROSS WEIGHT":
            # Container-table header (incl. the bare GROSS WEIGHT trap:
            # real weights arrive later as TOTAL summary colon rows).
            index += 1
            continue
        field, remainder = _label_prefix_field(row)
        if field is None:
            index += 1
            continue
        value_parts = [remainder] if remainder else []
        start = index
        index += 1
        while index < len(rows):
            following = rows[index]
            if ":" in following or _known_label_start(following):
                break
            value_parts.append(following.strip())
            index += 1
        joined = "; ".join(part for part in value_parts if part)
        if joined and not values.get(field):
            values[field] = "" if _is_placeholder(joined) else joined
            anchors[field].extend(range(start, index))

    extracted = ExtractedFields(
        shipper=values.get("shipper", ""),
        consignee=values.get("consignee", ""),
        notify_party=values.get("notify_party", ""),
        port_of_loading=values.get("port_of_loading", ""),
        port_of_discharge=values.get("port_of_discharge", ""),
        container_count=values.get("container_count", ""),
        gross_weight_kg=values.get("gross_weight_kg", ""),
    )
    return extracted, anchors


def extract_fields(document: ParsedDocument) -> ExtractedFields:
    """Extract the seven canonical fields from one parsed document.

    Thin wrapper over :func:`extract_fields_anchored` (anchored extraction): the
    signature, return value and behavior are unchanged — only the row
    anchors are dropped. Kept as the stable public entry point for the
    review stage and existing callers.

    Args:
        document: A parser output (``rows`` carry ``Label: value`` strings
            and/or bare-label blocks; ``text`` backs bare pdf tables).

    Returns:
        An :class:`~models.ExtractedFields` record; fields absent from the
        document remain blank.

    Example:
        >>> doc = ParsedDocument(
        ...     path="attachments/a_SI.txt",
        ...     fmt="txt",
        ...     kind="SI",
        ...     text="Shipper: ACME\\nConsignee: ORBIS\\nPOL: BUATAN",
        ...     rows=("Shipper: ACME", "Consignee: ORBIS", "POL: BUATAN"),
        ... )
        >>> fields = extract_fields(doc)
        >>> (fields.shipper, fields.consignee, fields.port_of_loading)
        ('ACME', 'ORBIS', 'BUATAN')
        >>> fields.missing()
        ['notify_party', 'port_of_discharge', 'container_count', 'gross_weight_kg']
    """
    return extract_fields_anchored(document)[0]


def _label_prefix_field(row: str) -> tuple[str | None, str]:
    """Longest mapped-label prefix of a colon-less row.

    Returns ``(field, remainder)`` where ``remainder`` is the inline value
    for glued lines (``Consignee (Non-Negotiable) BALL & DOGGETT …``) or
    ``""`` for pure bare labels (``Shipper``).

    Example:
        >>> _label_prefix_field("Consignee (Non-Negotiable) BALL & DOGGETT")
        ('consignee', 'BALL & DOGGETT')
        >>> _label_prefix_field("Shipper")
        ('shipper', '')
        >>> _label_prefix_field("APRIL FINE PAPER TRADING")
        (None, 'APRIL FINE PAPER TRADING')
    """
    words = row.split()
    for count in range(len(words), 0, -1):
        prefix = " ".join(words[:count])
        field = field_for_label(prefix)
        if field:
            return field, " ".join(words[count:])
    return None, row


def _known_label_start(row: str) -> bool:
    """True when the row starts with any known label (mapped or not).

    Example:
        >>> _known_label_start("Export Carrier (vessel, voyage)SOLID 16")
        True
        >>> _known_label_start("BUATAN, INDONESIA")
        False
    """
    words = row.split()
    for count in range(len(words), 0, -1):
        prefix = " ".join(words[:count])
        if field_for_label(prefix) or normalize_label(prefix) in _NON_FIELD_LABELS:
            return True
    return False


def assign_roles(documents: list[ParsedDocument]) -> ParsedDocument | None:
    """Pick the SI (reference) document from a parsed attachment pair.

    The SI announces itself: its title is a shipping-instruction variant
    (``SHIPPING INSTRUCTION``, ``BILL OF LADING INSTRUCTION``,
    ``BL INSTRUCTION``), which parsers already map to ``kind="SI"``. The
    remaining document is the draft BL. Ties and ambiguities return
    ``None`` (the caller escalates per review policy).

    Args:
        documents: The parsed attachments of one email (2 for a
            comparison; anything else is not a verifiable pair).

    Returns:
        The SI document, or ``None`` when roles cannot be assigned.

    Example:
        >>> si = ParsedDocument(path="a.txt", fmt="txt", kind="SI")
        >>> bl = ParsedDocument(path="b.txt", fmt="txt", kind="BL")
        >>> assign_roles([si, bl]) is si
        True
        >>> assign_roles([bl]) is None
        True
    """
    if len(documents) != 2:
        return None
    si_docs = [doc for doc in documents if doc.kind == "SI"]
    if len(si_docs) == 1:
        return si_docs[0]
    return None
