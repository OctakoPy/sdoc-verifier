import sdoc_verifier
from sdoc_verifier.llm import load_api_keys, resolve_models


def test_package_exports_canonical_fields() -> None:
    assert sdoc_verifier.FIELDS[0] == "shipper"
    assert sdoc_verifier.FIELDS[-1] == "gross_weight_kg"


def test_key_parsing_is_explicit_and_local() -> None:
    assert load_api_keys("a, b,,c") == ["a", "b", "c"]
    assert resolve_models()
