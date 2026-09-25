from pathlib import Path

from sdoc_verifier.parsers import parse_attachment
from sdoc_verifier.pipeline import load_emails, run_pipeline


def test_demo_has_expected_conservative_outcomes(demo_root: Path) -> None:
    records, traces = run_pipeline(load_emails(demo_root), data_root=demo_root)
    results = {record.email_id: record for record in records}
    assert results["email_001"].status == "OK"
    assert results["email_002"].status == "MISMATCH"
    assert "container_count" in results["email_002"].mismatch_fields
    assert results["email_003"].review_reason == "missing_value"
    assert results["email_004"].review_reason == "unreadable"
    assert results["email_005"].review_reason == "wrong_doc_type"
    assert results["email_006"].category == "GENERAL"
    assert results["email_007"].review_reason == "unreadable"
    assert results["email_008"].review_reason == "unreadable"
    assert results["email_009"].category == "SI_REQUEST"
    assert results["email_010"].status == "OK"
    assert len(records) == 10
    assert len(traces) == 10
    assert traces[0].stage("classify") is not None
    assert traces[0].stage("extract") is not None
    assert traces[0].stage("compare") is not None


def test_attachment_paths_cannot_escape_data_root(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    (root / "inbox").mkdir(parents=True)
    (root / "inbox" / "email_001.json").write_text(
        '{"email_id":"email_001","subject":"Draft BL",'
        '"body":"compare the SI and draft BL",'
        '"attachments":["../secret.txt","../other.txt"]}',
        encoding="utf-8",
    )
    records, traces = run_pipeline(load_emails(root), data_root=root)
    assert records[0].status == "NEEDS_REVIEW"
    assert records[0].review_reason == "unreadable"
    assert traces[0].stage("parse") is not None


def test_read_failure_is_kept_in_document_list(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    (root / "inbox").mkdir(parents=True)
    (root / "inbox" / "email_001.json").write_text(
        '{"email_id":"email_001","subject":"Draft BL",'
        '"body":"compare the SI and draft BL",'
        '"attachments":["missing-si.txt","missing-bl.txt"]}',
        encoding="utf-8",
    )
    records, _ = run_pipeline(load_emails(root), data_root=root)
    assert records[0].review_reason == "unreadable"


def test_parser_is_not_called_with_optional_keys_by_default(demo_root: Path) -> None:
    path = demo_root / "attachments" / "si_scan.pdf"
    document, _ = parse_attachment("attachments/si_scan.pdf", path.read_bytes())
    assert document.kind == "UNREADABLE"
