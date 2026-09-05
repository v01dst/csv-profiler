"""csv-profiler — profile any CSV: types, stats, nulls, uniques. Pure stdlib."""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import dataclass, field


@dataclass
class ColumnProfile:
    name: str
    inferred_type: str
    total: int
    nulls: int
    empty_strings: int
    unique: int
    distinct_ratio: float
    numeric: dict = field(default_factory=dict)
    top_values: list = field(default_factory=list)
    min_length: int | None = None
    max_length: int | None = None


TYPE_ORDER = ("integer", "float", "boolean", "date", "string")


def looks_like_int(value: str) -> bool:
    if value.lstrip("+-").isdigit():
        return True
    return False


def looks_like_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def looks_like_bool(value: str) -> bool:
    return value.lower() in ("true", "false", "yes", "no", "y", "n", "t", "f")


def looks_like_date(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 3:
        return False
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return 1000 <= year <= 9999 and 1 <= month <= 12 and 1 <= day <= 31
    except ValueError:
        return False


def infer_column_type(values: list[str]) -> str:
    non_empty = [v for v in values if v.strip() != ""]
    if not non_empty:
        return "empty"
    for t in TYPE_ORDER:
        checker = {
            "integer": looks_like_int,
            "float": looks_like_float,
            "boolean": looks_like_bool,
            "date": looks_like_date,
        }.get(t)
        if checker is None or all(checker(v) for v in non_empty):
            return t
    return "string"


def profile_column(name: str, values: list[str], top_n: int = 5) -> ColumnProfile:
    total = len(values)
    nulls = sum(1 for v in values if v is None)
    empty = sum(1 for v in values if v == "")
    non_null = [v for v in values if v is not None and v != ""]
    uniques = set(non_null)
    inferred = infer_column_type(non_null)

    profile = ColumnProfile(
        name=name,
        inferred_type=inferred,
        total=total,
        nulls=nulls,
        empty_strings=empty,
        unique=len(uniques),
        distinct_ratio=round(len(uniques) / len(non_null), 4) if non_null else 0.0,
    )

    if inferred in ("integer", "float"):
        nums = [float(v) for v in non_null]
        mean = sum(nums) / len(nums)
        variance = sum((x - mean) ** 2 for x in nums) / len(nums)
        profile.numeric = {
            "min": min(nums),
            "max": max(nums),
            "mean": round(mean, 4),
            "stddev": round(math.sqrt(variance), 4),
            "sum": sum(nums),
        }

    counts: dict[str, int] = {}
    for v in non_null:
        counts[v] = counts.get(v, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    profile.top_values = [[v, c] for v, c in ranked[:top_n]]

    lengths = [len(v) for v in non_null]
    if lengths:
        profile.min_length = min(lengths)
        profile.max_length = max(lengths)

    return profile


def profile_csv(path: str, delimiter: str = ",", top_n: int = 5, columns: list[str] | None = None) -> dict:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = list(reader)
    if not rows:
        raise ValueError("csv is empty")
    header, data = rows[0], rows[1:]
    columns_all: dict[str, list[str]] = {h: [] for h in header}
    for row in data:
        for i, h in enumerate(header):
            columns_all[h].append(row[i] if i < len(row) else None)
    selected = columns if columns else list(columns_all.keys())
    missing = [c for c in selected if c not in columns_all]
    if missing:
        raise ValueError(f"unknown column(s): {', '.join(missing)}")
    profiles = [profile_column(h, columns_all[h], top_n) for h in selected]
    return {
        "file": path,
        "rows": len(data),
        "columns": len(selected) if columns else len(header),
        "profiles": [p.__dict__ for p in profiles],
    }


def render_report(result: dict) -> str:
    lines = []
    lines.append(f"file: {result['file']}")
    lines.append(f"rows: {result['rows']}  columns: {result['columns']}")
    lines.append("")
    for p in result["profiles"]:
        lines.append(f"[{p['name']}]  type={p['inferred_type']}  nulls={p['nulls']}  empty={p['empty_strings']}  unique={p['unique']} ({p['distinct_ratio']*100:.1f}%)")
        if p["numeric"]:
            n = p["numeric"]
            lines.append(f"  min={n['min']}  max={n['max']}  mean={n['mean']}  stddev={n['stddev']}  sum={n['sum']}")
        if p["min_length"] is not None and p["inferred_type"] == "string":
            lines.append(f"  length: min={p['min_length']}  max={p['max_length']}")
        if p["top_values"]:
            tops = ", ".join(f"{v!r} x{c}" for v, c in p["top_values"][:3])
            lines.append(f"  top: {tops}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    delimiter = ","
    top_n = 5
    as_json = False
    columns: list[str] | None = None
    path: str | None = None

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-d", "--delimiter") and i + 1 < len(args):
            delimiter = args[i + 1]
            i += 2
            continue
        if a == "--tsv":
            delimiter = "\t"
            i += 1
            continue
        if a == "--json":
            as_json = True
            i += 1
            continue
        if a == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])
            i += 2
            continue
        if a in ("-c", "--columns") and i + 1 < len(args):
            columns = [c.strip() for c in args[i + 1].split(",") if c.strip()]
            i += 2
            continue
        if a in ("-h", "--help"):
            print("csv-profiler [--json] [--tsv | -d SEP] [--top N] <file.csv>")
            return 0
        path = a
        i += 1

    if not path:
        print("error: no csv file given", file=sys.stderr)
        return 2
    try:
        result = profile_csv(path, delimiter, top_n, columns)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
