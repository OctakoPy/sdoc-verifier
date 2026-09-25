from sdoc_verifier.classify import Email, classify_email, decide


def test_subject_rules_precede_body_rules() -> None:
    category, confidence = decide(
        "Draft BL comparison",
        "Please send the draft BL after checking the SI.",
    )
    assert category == "BL_COMPARISON"
    assert confidence.score == 0.95


def test_comparison_body_rule() -> None:
    category, confidence = classify_email(
        Email("Operations note", "Please compare the SI and draft BL.")
    )
    assert category == "BL_COMPARISON"
    assert confidence.score == 0.85


def test_non_comparison_fallback() -> None:
    category, confidence = classify_email(Email("Hello", "A general operations note."))
    assert category == "GENERAL"
    assert confidence.score == 0.55
