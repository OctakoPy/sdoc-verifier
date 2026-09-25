from pathlib import Path

import pytest

DEMO_ROOT = Path(__file__).resolve().parents[1] / "demo"


@pytest.fixture(name="demo_root")
def demo_root_fixture() -> Path:
    return DEMO_ROOT
