"""PDF parser for native text, scans, and unreadable files.

Native text is normalized into the shared row contract. A scan is marked
unreadable unless the caller explicitly supplies the optional Gemini OCR
adapter. Corrupt files return the same unreadable shape instead of raising.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from sdoc_verifier.models import Confidence, DocKind, ParsedDocument

__all__ = ["parse_pdf", "parse_pdf_bytes"]

#: Minimum extracted characters for the text layer to count as usable.
MIN_NATIVE_CHARS = 40

#: Phrases that mark a document as the *shipping instruction* side. Checked
#: before the BL phrases because "BILL OF LADING INSTRUCTION" contains the
#: BL phrase as a substring — the same trap the xlsx banner rule handles.
_SI_PHRASES: tuple[str, ...] = (
    "SHIPPING INSTRUCTION",
    "BILL OF LADING INSTRUCTION",
    "BL INSTRUCTION",
)
_BL_PHRASES: tuple[str, ...] = (
    "BILL OF LADING (DRAFT)",
    "DRAFT BILL OF LADING",
    "BILL OF LADING",
)

_RULE_LINE_ENDSWITH = ("====", "----")


def _kind_hint(rows: tuple[str, ...]) -> DocKind:
    """Document-kind hint from the first rows of extracted PDF text.

    Example:
        >>> _kind_hint(("BILL OF LADING INSTRUCTION", "B/L NUMBER: X"))
        'SI'
        >>> _kind_hint(("BILL OF LADING (DRAFT)", "B/L NUMBER: X"))
        'BL'
        >>> _kind_hint(("PAGE 1", "SOME CONTENT"))
        'OTHER'
    """
    for row in rows[:6]:
        upper = row.upper()
        if any(phrase in upper for phrase in _SI_PHRASES):
            return "SI"
        if any(phrase in upper for phrase in _BL_PHRASES):
            return "BL"
    return "OTHER"


def _looks_like_title(line: str) -> bool:
    """True when a line reads as a document title rather than a label row.

    Example:
        >>> _looks_like_title("BILL OF LADING (DRAFT)")
        True
        >>> _looks_like_title("Shipper: A")
        False
    """
    return ":" not in line


def _content_rows(lines: list[str]) -> tuple[str, ...]:
    """Drop the title line and rule lines, keep the rest verbatim.

    Only the first non-empty, non-rule line is a title candidate; later
    colon-less lines are content (e.g. multi-line addresses).

    Example:
        >>> _content_rows(["BILL OF LADING (DRAFT)", "====", "Shipper"])
        ('Shipper',)
        >>> _content_rows(["TITLE", "NOT A RULE BUT CONTENT"])
        ('NOT A RULE BUT CONTENT',)
    """
    rows: list[str] = []
    seen_first = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith(_RULE_LINE_ENDSWITH):
            continue
        if not seen_first:
            seen_first = True
            if _looks_like_title(stripped):
                continue
        rows.append(stripped)
    return tuple(rows)


def _unreadable(
    path: str, error: str, *, scanned: bool, confidence: float, reason: str
) -> tuple[ParsedDocument, Confidence]:
    """Build the shared UNREADABLE outcome for the pdf parser."""
    document = ParsedDocument(
        path=path,
        fmt="pdf",
        kind="UNREADABLE",
        text="",
        rows=(),
        scanned=scanned,
        error=error,
    )
    return document, Confidence(confidence, reason)


def parse_pdf_bytes(
    path: str, data: bytes, *, gemini_keys: list[str] | None = None
) -> tuple[ParsedDocument, Confidence]:
    """Parse raw ``.pdf`` bytes into a document + confidence pair.

    Args:
        path: Attachment path exactly as listed in the email JSON.
        data: Raw file bytes (the caller read them from disk).
        gemini_keys: Rotated Gemini API keys (``GEMINI_API_KEYS``). When the
            PDF has no text layer and keys are provided, the page is
            transcribed via :func:`sdoc_verifier.llm.ocr_pdf_pages_bytes`
            (optional OCR policy); when absent, the scanned document comes back
            ``UNREADABLE`` at confidence 0.25 for review to escalate.

    Returns:
        ``(document, confidence)`` with ``fmt="pdf"``. Corrupt files and
        unusable scans return ``kind="UNREADABLE"`` with an ``error``
        string instead of raising.
    """
    import pymupdf

    try:
        with pymupdf.open(stream=data, filetype="pdf") as document_handle:
            parts: list[str] = []
            for page in document_handle.pages():
                parts.append(str(page.get_text()))
            text = "\n".join(parts)
    except Exception as exc:  # noqa: BLE001 - any open error is "unreadable"
        return _unreadable(
            path,
            f"cannot open pdf: {exc}",
            scanned=False,
            confidence=0.1,
            reason="corrupt or unsupported pdf",
        )

    stripped = text.strip()
    if len(stripped) < MIN_NATIVE_CHARS:
        # No usable text layer -> scanned. OCR when configured (optional OCR policy).
        if gemini_keys:
            from sdoc_verifier.llm import ocr_pdf_pages_bytes

            document, confidence = ocr_pdf_pages_bytes(path, data, gemini_keys)
            if document.kind != "UNREADABLE":
                # Refine the kind hint from the transcription's title lines
                # (llm.py returns OTHER by design; this module owns the
                # SI/BL phrase lists, incl. the BL-INSTRUCTION trap).
                kind = _kind_hint(tuple(document.text.splitlines()))
                document = replace(document, kind=kind)
            return document, confidence
        return _unreadable(
            path,
            "no text layer (scanned); OCR keys not configured",
            scanned=True,
            confidence=0.25,
            reason="scanned pdf without OCR",
        )

    lines = stripped.splitlines()
    rows = _content_rows(lines)
    kind = _kind_hint(tuple(lines))
    document = ParsedDocument(
        path=path,
        fmt="pdf",
        kind=kind,
        text=stripped,
        rows=rows,
        scanned=False,
        error=None,
    )
    return document, Confidence(0.9, f"native text layer, kind hint {kind}")


def parse_pdf(
    path: str | Path, *, gemini_keys: list[str] | None = None
) -> tuple[ParsedDocument, Confidence]:
    """Parse one ``.pdf`` attachment from disk.

    Missing files return an ``UNREADABLE`` document (confidence 0.1) rather
    than raising, mirroring the other parsers' error contract.

    Args:
        path: Filesystem path of the attachment.
        gemini_keys: Optional rotated Gemini API keys (see
            :func:`parse_pdf_bytes`).

    Returns:
        ``(document, confidence)`` as in :func:`parse_pdf_bytes`.

    Example:
        >>> import pymupdf, tempfile, os
        >>> doc = pymupdf.open()
        >>> page = doc.new_page()
        >>> _ = page.insert_text((72, 72), "SHIPPING INSTRUCTION")
        >>> _ = page.insert_text((72, 92), "Shipper: ACME LTD")
        >>> _ = page.insert_text((72, 112), "Consignee: ORBIS TRADING CO")
        >>> _ = page.insert_text((72, 132), "Port of Loading: BUATAN, INDONESIA")
        >>> fd, tmp = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
        >>> doc.save(tmp); doc.close()
        >>> parsed, conf = parse_pdf(tmp)
        >>> (parsed.fmt, parsed.kind, parsed.rows[0])
        ('pdf', 'SI', 'Shipper: ACME LTD')
        >>> conf.score
        0.9
        >>> os.unlink(tmp)
    """
    source = Path(path)
    try:
        data = source.read_bytes()
    except OSError as exc:
        return _unreadable(
            str(path),
            f"cannot read file: {exc}",
            scanned=False,
            confidence=0.1,
            reason="unreadable file",
        )
    return parse_pdf_bytes(str(path), data, gemini_keys=gemini_keys)
