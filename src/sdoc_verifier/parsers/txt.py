"""Parser for plain-text attachments with line-based label/value rows."""

from __future__ import annotations

import re

from sdoc_verifier.models import Confidence, DocKind, ParsedDocument

__all__ = ["detect_kind", "parse_txt"]

# Continuation lines: indented (space/tab) non-empty lines that belong to
# the preceding label line.
_CONTINUATION = re.compile(r"^[ \t]+\S")

#: First-line document-kind headers seen in the sample documents (row format).
#: Case-insensitive substring match. ``SHIPPING INSTRUCTION`` is listed
#: before the bare ``SI`` abbreviation so the specific phrase wins; a doc
#: titled ``BL INSTRUCTION`` (an SI variant) must not match ``BILL OF
#: LADING``, and it does not (no ``BILL OF LADING`` substring).
_SI_HEADERS: tuple[str, ...] = ("SHIPPING INSTRUCTION",)
_BL_HEADERS: tuple[str, ...] = ("BILL OF LADING",)

# Anything outside ASCII whitespace/printable/Latin-1 range is treated as
# binary garbage (decoded with errors="replace" upstream, so U+FFFD counts)
# — except CJK ideographs, which are legitimate document text (language routing
# multilingual fixtures; annotation glosses were already Latin-1-adjacent
# in docx, and native-ZH txt documents must survive this gate to reach the
# language router).
_GARBLED_RE = re.compile(r"[^\t\n\r\x20-\x7e\xa0-\xff\u3400-\u4dbf\u4e00-\u9fff]")

# Decorative rule lines (e.g. "====", "----"): structure, not fields.
_RULE_LINE = re.compile(r"^[=\-_*]{3,}$")


def detect_kind(first_line: str) -> DocKind:
    """Return the SI/BL kind hint for a document header line.

    Case-insensitive substring match on the header. Returns ``"SI"`` or
    ``"BL"`` on a header hit, else ``"OTHER"``.

    Example:
        >>> detect_kind("BILL OF LADING (DRAFT)")
        'BL'
        >>> detect_kind("Shipping Instruction")
        'SI'
        >>> detect_kind("COMMERCIAL INVOICE")
        'OTHER'
    """
    head = first_line.strip().upper()
    if any(marker in head for marker in _SI_HEADERS):
        return "SI"
    if any(marker in head for marker in _BL_HEADERS):
        return "BL"
    return "OTHER"


def _looks_garbled(text: str) -> bool:
    """True when the decoded text is unusable (empty or mostly binary)."""
    if not text.strip():
        return True
    bad = len(_GARBLED_RE.findall(text))
    return bad > max(4, len(text) // 20)


def _looks_like_title(line: str) -> bool:
    """True when a line is a document title rather than a label row.

    Titles are short, carry no ``Label: value`` colon, and are not
    continuations (``BILL OF LADING (DRAFT)`` vs ``Shipper: A``).

    Example:
        >>> _looks_like_title("BILL OF LADING (DRAFT)")
        True
        >>> _looks_like_title("Shipper: A")
        False
    """
    stripped = line.strip()
    return ":" not in stripped and not _CONTINUATION.match(line)


def _fold_continuations(lines: list[str]) -> tuple[str, ...]:
    """Fold indented continuation lines onto their preceding label line.

    Skips the document title (first non-empty title-like line) and rule
    lines so rows contain only ``Label: value`` field content.

    Example:
        >>> _fold_continuations(
        ...     ["SHIPPING INSTRUCTION", "====", "Shipper: A", "  addr", "Port: B"]
        ... )
        ('Shipper: A addr', 'Port: B')
    """
    rows: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        if _RULE_LINE.match(line.strip()):
            continue
        if not rows and _looks_like_title(line):
            continue
        if _CONTINUATION.match(line) and rows:
            rows[-1] = f"{rows[-1]} {line.strip()}"
        else:
            rows.append(line.strip())
    return tuple(rows)


def parse_txt(path: str, text: str) -> tuple[ParsedDocument, Confidence]:
    """Parse the decoded text of one ``.txt`` attachment.

    Args:
        path: Attachment path exactly as listed in the email JSON, kept
            verbatim on the result for traceability.
        text: Attachment bytes already decoded (UTF-8, errors replaced).

    Returns:
        ``(document, confidence)`` — a :class:`ParsedDocument` with
        ``fmt="txt"``, a header-derived kind hint and folded rows, plus the
        parse-stage confidence (0.95 clean, 0.1 garbled/empty).

    Example:
        >>> doc, conf = parse_txt("attachments/x_BL.txt", "")
        >>> (doc.kind, doc.error, conf.score)
        ('UNREADABLE', 'no usable text (empty or garbled)', 0.1)
    """
    if _looks_garbled(text):
        document = ParsedDocument(
            path=path,
            fmt="txt",
            kind="UNREADABLE",
            text=text,
            rows=(),
            scanned=False,
            error="no usable text (empty or garbled)",
        )
        return document, Confidence(0.1, "empty or garbled text")

    lines = text.splitlines()
    first = next((ln for ln in lines if ln.strip()), "")
    kind = detect_kind(first)
    rows = _fold_continuations(lines)
    document = ParsedDocument(
        path=path,
        fmt="txt",
        kind=kind,
        text=text,
        rows=rows,
        scanned=False,
        error=None,
    )
    return document, Confidence(
        0.95, f"clean text: {len(rows)} row(s), kind hint {kind}"
    )
