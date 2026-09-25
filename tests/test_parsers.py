from pathlib import Path

from sdoc_verifier.parsers import parse_attachment


def test_txt_pair_is_readable(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_match.txt"
    document, confidence = parse_attachment(
        "attachments/si_match.txt", path.read_bytes()
    )
    assert document.kind == "SI"
    assert document.fmt == "txt"
    assert confidence.score > 0.9


def test_docx_pair_is_readable(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_mismatch.docx"
    document, confidence = parse_attachment(
        "attachments/si_mismatch.docx", path.read_bytes()
    )
    assert document.kind == "SI"
    assert document.fmt == "docx"
    assert len(document.rows) >= 7
    assert confidence.score > 0.8


def test_xlsx_is_readable(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_missing.xlsx"
    document, confidence = parse_attachment(
        "attachments/si_missing.xlsx", path.read_bytes()
    )
    assert document.kind == "SI"
    assert document.fmt == "xlsx"
    assert confidence.score > 0.8


def test_native_pdf_is_readable(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_native.pdf"
    document, confidence = parse_attachment(
        "attachments/si_native.pdf", path.read_bytes()
    )
    assert document.kind == "SI"
    assert document.fmt == "pdf"
    assert confidence.score > 0.8


def test_scanned_pdf_requires_explicit_ocr(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_scan.pdf"
    document, confidence = parse_attachment(
        "attachments/si_scan.pdf", path.read_bytes()
    )
    assert document.kind == "UNREADABLE"
    assert document.scanned is True
    assert confidence.score < 0.3


def test_translation_requires_explicit_opt_in(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_translation.txt"
    document, confidence = parse_attachment(
        "attachments/si_translation.txt", path.read_bytes()
    )
    assert document.kind == "UNREADABLE"
    assert document.error == "optional label translation not enabled"
    assert confidence.score == 0.1


def test_optional_translation_uses_injected_seam(demo_root: Path, monkeypatch) -> None:
    from sdoc_verifier import llm

    monkeypatch.setattr(
        llm,
        "_generate_text",
        lambda key, text, model: (
            "SHIPPING INSTRUCTION\nShipper: A\nConsignee: B\nPort of Loading: C"
        ),
    )
    path = demo_root / "attachments" / "si_translation.txt"
    document, confidence = parse_attachment(
        "attachments/si_translation.txt", path.read_bytes(), gemini_keys=["test"]
    )
    assert document.kind == "SI"
    assert document.translated is True
    assert confidence.score == 0.85


def test_optional_ocr_uses_injected_seam(demo_root: Path, monkeypatch) -> None:
    from sdoc_verifier import llm

    monkeypatch.setattr(
        llm,
        "_generate",
        lambda key, data, model: (
            "SHIPPING INSTRUCTION\nShipper: A\nConsignee: B\nPort of Loading: C"
        ),
    )
    path = demo_root / "attachments" / "si_scan.pdf"
    document, confidence = parse_attachment(
        "attachments/si_scan.pdf", path.read_bytes(), gemini_keys=["test"]
    )
    assert document.kind == "SI"
    assert document.scanned is True
    assert confidence.score == 0.85
