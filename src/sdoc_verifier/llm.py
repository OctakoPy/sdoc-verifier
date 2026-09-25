"""Optional Gemini adapters for OCR and experimental label translation."""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from sdoc_verifier.models import Confidence, ParsedDocument

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_MODELS = [DEFAULT_GEMINI_MODEL]
OCR_PROMPT = (
    "Transcribe this shipping document exactly. Preserve line structure and "
    "output raw text only."
)
TRANSLATION_PROMPT = (
    "Translate only the document title and field labels into standard English "
    "shipping terminology. Keep every value, number, and line unchanged. "
    "Output raw text only."
)


def load_api_keys(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def load_api_keys_from_env() -> list[str]:
    """Read explicitly exported keys without loading a configuration file."""
    return load_api_keys(os.environ.get("GEMINI_API_KEYS", ""))


def resolve_models() -> list[str]:
    raw_models = os.environ.get("GEMINI_MODELS", "")
    if raw_models.strip():
        return [item.strip() for item in raw_models.split(",") if item.strip()]
    pinned = os.environ.get("GEMINI_MODEL", "").strip()
    return [pinned] if pinned else list(DEFAULT_GEMINI_MODELS)


def _generate(api_key: str, pdf_bytes: bytes, model: str) -> str:
    google = cast(Any, importlib.import_module("google.genai"))
    types = cast(Any, importlib.import_module("google.genai.types"))
    client = google.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            OCR_PROMPT,
        ],
    )
    return response.text or ""


def _generate_text(api_key: str, text: str, model: str) -> str:
    google = cast(Any, importlib.import_module("google.genai"))
    client = google.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[text, TRANSLATION_PROMPT],
    )
    return response.text or ""


def _rotate(keys: list[str], operation: Callable[[str, str], str]) -> str:
    for model in resolve_models():
        for key in keys:
            try:
                result = operation(key, model)
            except Exception as exc:
                logger.warning(
                    "Gemini attempt failed for model %s: %s",
                    model,
                    type(exc).__name__,
                )
                continue
            if result.strip():
                return result.strip()
    raise RuntimeError("all configured Gemini attempts failed")


def ocr_pdf_pages_bytes(
    path: str, data: bytes, keys: list[str]
) -> tuple[ParsedDocument, Confidence]:
    if not keys:
        return (
            ParsedDocument(
                path=path,
                fmt="pdf",
                kind="UNREADABLE",
                scanned=True,
                error="OCR is not enabled for this local run",
            ),
            Confidence(0.1, "optional OCR is not enabled"),
        )
    try:
        text = _rotate(keys, lambda key, model: _generate(key, data, model))
    except RuntimeError:
        return (
            ParsedDocument(
                path=path,
                fmt="pdf",
                kind="UNREADABLE",
                scanned=True,
                error="OCR service unavailable",
            ),
            Confidence(0.1, "optional OCR unavailable; manual review required"),
        )
    rows = tuple(line.strip() for line in text.splitlines() if line.strip())
    return (
        ParsedDocument(
            path=path,
            fmt="pdf",
            kind="OTHER",
            text=text,
            rows=rows,
            scanned=True,
        ),
        Confidence(0.85, "Gemini OCR transcription"),
    )


def ocr_pdf_pages(
    path: str | Path, keys: list[str]
) -> tuple[ParsedDocument, Confidence]:
    source = Path(path)
    try:
        data = source.read_bytes()
    except OSError:
        return (
            ParsedDocument(
                path=str(path),
                fmt="pdf",
                kind="UNREADABLE",
                scanned=True,
                error="attachment could not be read",
            ),
            Confidence(0.1, "unreadable file"),
        )
    return ocr_pdf_pages_bytes(str(path), data, keys)


def translate_to_english(text: str, keys: list[str]) -> str:
    if not keys:
        raise RuntimeError("label translation requires explicit Gemini opt-in")
    return _rotate(keys, lambda key, model: _generate_text(key, text, model))


__all__ = [
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_GEMINI_MODELS",
    "OCR_PROMPT",
    "TRANSLATION_PROMPT",
    "load_api_keys",
    "load_api_keys_from_env",
    "ocr_pdf_pages",
    "ocr_pdf_pages_bytes",
    "resolve_models",
    "translate_to_english",
]
