#!/usr/bin/env python3
"""Run the local SDOC verifier and print decisions to stdout."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from sdoc_verifier.llm import load_api_keys_from_env
from sdoc_verifier.pipeline import load_emails, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="demo", help="local fixture root")
    parser.add_argument(
        "--gemini",
        action="store_true",
        help="explicitly enable optional OCR or label translation",
    )
    parser.add_argument(
        "--json", action="store_true", help="print machine-readable JSON"
    )
    args = parser.parse_args()

    keys = load_api_keys_from_env() if args.gemini else []
    if args.gemini and not keys:
        print(
            "Gemini opt-in requested but GEMINI_API_KEYS is empty; "
            "staying deterministic."
        )
    records, traces = run_pipeline(
        load_emails(Path(args.data)),
        data_root=Path(args.data),
        gemini_keys=keys,
    )
    if args.json:
        payload = {
            "records": [asdict(record) for record in records],
            "traces": [asdict(trace) for trace in traces],
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return

    print(f"Processed {len(records)} email(s) from {args.data}")
    for record in records:
        detail = record.review_reason or record.status
        fields = ", ".join(record.mismatch_fields) or "none"
        print(
            f"{record.email_id}: {record.category} -> {record.status} "
            f"({detail}; mismatch fields: {fields}; by {record.decided_by})"
        )


if __name__ == "__main__":
    main()
