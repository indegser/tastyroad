#!/usr/bin/env python3
"""Apply reviewed copy-only repairs without replacing menu or evidence rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from apply_must_taste_result import validate_repaired_reason_text
from must_taste_schema import DEFAULT_SQLITE


def row_fingerprint(row: dict) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def repair_copy(sqlite_path: Path, manifest: dict, *, apply: bool = False) -> dict:
    fixes = manifest["fixes"]
    ids = [fix["id"] for fix in fixes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate repair IDs")
    target = sqlite_path.resolve().as_uri() + ("?mode=rw" if apply else "?mode=ro")
    connection = sqlite3.connect(target, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        updates = []
        for fix in fixes:
            row = connection.execute(
                "SELECT * FROM video_must_taste_items WHERE id = ?", (fix["id"],)
            ).fetchone()
            if row is None or row_fingerprint(dict(row)) != fix["row_sha256"]:
                raise ValueError(f"Stale or missing source row: {fix['id']}")
            if row["repaired_reason"] != fix["before"]:
                raise ValueError(f"Before copy mismatch: {fix['id']}")
            after = fix["after"]
            if not isinstance(after, str) or not after.strip() or after != after.strip():
                raise ValueError(f"Invalid display text: {fix['id']}")
            if any(char in after for char in "\n\r") or after == fix["before"]:
                raise ValueError(f"Unchanged or multiline display text: {fix['id']}")
            validate_repaired_reason_text(row["rank"], after, row["reason"])
            if fix.get("review", {}).get("verdict") != "pass" or not fix.get("source_quote"):
                raise ValueError(f"Missing source/review artifact: {fix['id']}")
            evidence = json.loads(row["evidence_json"])
            if not isinstance(evidence, dict):
                raise ValueError(f"Invalid evidence object: {fix['id']}")
            evidence["repaired_reason"] = after
            updates.append((after, json.dumps(evidence, ensure_ascii=False), fix["id"]))
        if apply:
            connection.executemany(
                "UPDATE video_must_taste_items SET repaired_reason = ?, evidence_json = ? WHERE id = ?",
                updates,
            )
            connection.commit()
        else:
            connection.rollback()
        return {"mode": "apply" if apply else "dry-run", "rows": len(updates)}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(repair_copy(args.sqlite, json.loads(args.manifest.read_text()), apply=args.apply)))


if __name__ == "__main__":
    main()
