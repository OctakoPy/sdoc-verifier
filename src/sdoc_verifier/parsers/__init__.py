"""Format-dispatching attachment parsers and the readability gate."""

from __future__ import annotations

from pathlib import Path

from sdoc_verifier.models import Confidence, ParsedDocument
from sdoc_verifier.parsers.docx import parse_docx, parse_docx_bytes
from sdoc_verifier.parsers.lang import Language, detect_document_language
from sdoc_verifier.parsers.pdf import parse_pdf, parse_pdf_bytes
from sdoc_verifier.parsers.txt import _fold_continuations, detect_kind, parse_txt
from sdoc_verifier.parsers.xlsx import parse_xlsx, parse_xlsx_bytes

DEFAULT_MIN_TEXT_LEN = 20
MIN_ROWS_FOR_EXTRACTION = 3


def read_attachment_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _row_has_known_field(row: str) -> bool:
    from sdoc_verifier.extract import field_for_label

    if ":" in row:
        return field_for_label(row.partition(":")[0]) is not None
    words = row.split()
    return any(
        field_for_label(" ".join(words[:count])) is not None
        for count in range(len(words), 0, -1)
    )


def mark_unreadable(
    parsed: ParsedDocument,
    confidence: Confidence,
    min_text_len: int = DEFAULT_MIN_TEXT_LEN,
) -> tuple[ParsedDocument, Confidence]:
    """Demote documents that cannot support reliable field extraction."""
    if parsed.kind == "UNREADABLE":
        return parsed, confidence
    normalized = parsed.text.replace("\ufffd", "").strip()
    usable_rows = sum(1 for row in parsed.rows if _row_has_known_field(row))
    if len(normalized) < min_text_len:
        return _demote(
            parsed, "insufficient_text_layer", 0.1, "insufficient text layer"
        )
    if parsed.kind == "OTHER":
        return parsed, confidence
    if usable_rows < MIN_ROWS_FOR_EXTRACTION:
        return _demote(parsed, "insufficient_field_rows", 0.1, "too few field rows")
    return parsed, confidence


def _demote(
    document: ParsedDocument,
    error: str,
    score: float,
    reason: str,
) -> tuple[ParsedDocument, Confidence]:
    return (
        ParsedDocument(
            path=document.path,
            fmt=document.fmt,
            kind="UNREADABLE",
            text=document.text,
            rows=document.rows,
            scanned=document.scanned,
            translated=document.translated,
            error=error,
        ),
        Confidence(score, reason),
    )


def gate_parsed(
    parsed: ParsedDocument, confidence: Confidence
) -> tuple[ParsedDocument, Confidence]:
    return mark_unreadable(parsed, confidence)


def _maybe_translate(
    document: ParsedDocument,
    confidence: Confidence,
    *,
    gemini_keys: list[str],
) -> tuple[ParsedDocument, Confidence]:
    language: Language = detect_document_language(document.text)
    if language == "en":
        return document, confidence
    if not gemini_keys:
        return _demote(
            document,
            "optional label translation not enabled",
            0.1,
            f"non-English document ({language}) requires explicit translation opt-in",
        )
    from sdoc_verifier.llm import translate_to_english

    try:
        translated_text = translate_to_english(document.text, gemini_keys)
    except RuntimeError:
        return _demote(
            document,
            "label translation unavailable",
            0.1,
            f"label translation unavailable ({language}); manual review required",
        )
    lines = translated_text.splitlines()
    first = next((line for line in lines if line.strip()), "")
    translated = ParsedDocument(
        path=document.path,
        fmt=document.fmt,
        kind=detect_kind(first),
        text=translated_text,
        rows=_fold_continuations(lines),
        scanned=document.scanned,
        translated=True,
    )
    return mark_unreadable(
        translated,
        Confidence(0.85, f"Gemini label translation ({language} to en)"),
    )


def parse_attachment(
    path: str,
    data: bytes,
    *,
    gemini_keys: list[str] | None = None,
) -> tuple[ParsedDocument, Confidence]:
    """Parse one supported attachment and return a readability-gated result."""
    suffix = Path(path).suffix.lower()
    keys = gemini_keys or []
    if suffix == ".txt":
        document, confidence = parse_txt(path, read_attachment_text(data))
    elif suffix == ".xlsx":
        document, confidence = parse_xlsx_bytes(path, data)
    elif suffix == ".docx":
        document, confidence = parse_docx_bytes(path, data)
    elif suffix == ".pdf":
        document, confidence = parse_pdf_bytes(path, data, gemini_keys=keys or None)
    else:
        return (
            ParsedDocument(
                path=path,
                fmt="unknown",
                kind="UNREADABLE",
                error=f"unsupported attachment format: {suffix or '(none)'}",
            ),
            Confidence(0.1, "unsupported format"),
        )

    if document.kind != "UNREADABLE":
        document, confidence = _maybe_translate(document, confidence, gemini_keys=keys)
    return mark_unreadable(document, confidence)


__all__ = [
    "DEFAULT_MIN_TEXT_LEN",
    "MIN_ROWS_FOR_EXTRACTION",
    "detect_document_language",
    "detect_kind",
    "gate_parsed",
    "mark_unreadable",
    "parse_attachment",
    "parse_docx",
    "parse_docx_bytes",
    "parse_pdf",
    "parse_pdf_bytes",
    "parse_txt",
    "parse_xlsx",
    "parse_xlsx_bytes",
    "read_attachment_text",
]
