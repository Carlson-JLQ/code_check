#!/usr/bin/env python3
"""Expand canonical grouped CSA checker data into transient RAG records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def embedding_text(checker: dict[str, Any], logic: dict[str, Any]) -> str:
    frontend_by_id = {item["id"]: item["name"] for item in checker["frontends"]}
    behavior_parts = []
    for key, values in logic["behavior"].items():
        if values:
            behavior_parts.append(f"{key}: {'; '.join(values)}")
    return "\n".join(
        part
        for part in [
            f"checker: {checker['implementation_class']}",
            f"summary: {checker['summary']}",
            "frontends: " + ", ".join(frontend_by_id[item] for item in logic["applies_to_frontends"]),
            "callbacks: " + ", ".join(logic["callback_context"]),
            f"kind: {logic['kind']}",
            f"logic: {logic['meta_op']}",
            *behavior_parts,
        ]
        if part
    )


def expand_logic_units(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one in-memory record per unit, keyed only by its stable ID."""
    records = []
    for checker in data["checkers"]:
        frontend_by_id = {item["id"]: item for item in checker["frontends"]}
        for logic in checker["logic_units"]:
            records.append(
                {
                    "id": logic["id"],
                    "document": embedding_text(checker, logic),
                    "payload": {
                        "checker_id": checker["id"],
                        "implementation_class": checker["implementation_class"],
                        "summary": checker["summary"],
                        "analysis_mode": checker["analysis_mode"],
                        "frontends": [frontend_by_id[item] for item in logic["applies_to_frontends"]],
                        "callbacks": logic["callback_context"],
                        "kind": logic["kind"],
                        "meta_op": logic["meta_op"],
                        "behavior": logic["behavior"],
                        "meta_impl": logic["meta_impl"],
                        "source_spans": logic["source_spans"],
                        "api_refs": logic["api_refs"],
                        "depends_on": logic["depends_on"],
                    },
                }
            )
    ids = [item["id"] for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("logic unit IDs are not unique")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    records = expand_logic_units(json.loads(args.dataset.read_text(encoding="utf-8")))
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

