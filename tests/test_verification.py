from pathlib import Path

from sdoc_verifier.compare import compare_fields, normalize_value
from sdoc_verifier.extract import extract_fields, extract_fields_anchored
from sdoc_verifier.models import ExtractedFields, ParsedDocument
from sdoc_verifier.parsers import parse_attachment
from sdoc_verifier.review import review_comparison


def test_anchors_identify_source_rows() -> None:
    document = ParsedDocument(
        path="demo.txt",
        fmt="txt",
        kind="SI",
        text="Shipper: A\nConsignee: B\nPort of Loading: C",
        rows=("Shipper: A", "Consignee: B", "Port of Loading: C"),
    )
    fields, anchors = extract_fields_anchored(document)
    assert fields.shipper == "A"
    assert anchors["shipper"] == [0]
    assert anchors["port_of_loading"] == [2]


def test_normalization_handles_formatting_only_differences() -> None:
    si = ExtractedFields(
        shipper="Aster Paper | Harbor",
        container_count="2 x 40'HC",
        gross_weight_kg="18,400 KG",
    )
    bl = ExtractedFields(
        shipper="aster paper; harbor",
        container_count="2X40HC",
        gross_weight_kg="18400",
    )
    result = compare_fields(si, bl)
    assert normalize_value("gross_weight_kg", "18,400 KG") == "18400"
    assert not result.mismatch_fields()


def test_missing_value_is_escalated(demo_root: Path) -> None:
    si_path = demo_root / "attachments" / "si_missing.xlsx"
    bl_path = demo_root / "attachments" / "bl_missing.txt"
    si, _ = parse_attachment("attachments/si_missing.xlsx", si_path.read_bytes())
    bl, _ = parse_attachment("attachments/bl_missing.txt", bl_path.read_bytes())
    decision, comparison = review_comparison(2, [si, bl])
    assert decision.status == "NEEDS_REVIEW"
    assert decision.review_reason == "missing_value"
    assert comparison is None


def test_wrong_type_is_escalated(demo_root: Path) -> None:
    si, _ = parse_attachment(
        "attachments/si_wrong.txt",
        (demo_root / "attachments" / "si_wrong.txt").read_bytes(),
    )
    invoice, _ = parse_attachment(
        "attachments/invoice.txt",
        (demo_root / "attachments" / "invoice.txt").read_bytes(),
    )
    decision, comparison = review_comparison(2, [si, invoice])
    assert decision.status == "NEEDS_REVIEW"
    assert decision.review_reason == "wrong_doc_type"
    assert comparison is None


def test_extraction_keeps_missing_fields_blank() -> None:
    fields = extract_fields(
        ParsedDocument(
            path="partial.txt",
            fmt="txt",
            rows=("Shipper: A", "Consignee: B", "Port of Loading: C"),
        )
    )
    assert fields.missing()
    assert "gross_weight_kg" in fields.missing()
