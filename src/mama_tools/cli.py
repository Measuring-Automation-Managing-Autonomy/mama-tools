"""mama-tools command line interface.

Local-first and offline: every subcommand reads and writes files you own.
Nothing is sent anywhere. JSON output (--json) is provided for programmatic
use; the human output is plain text.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .errors import MamaToolsError
from .metrics import RATIO_CARDS, calculate
from .portfolio import build_view
from .registry import load_record, load_registry_dir, validate_record
from .series import append_series, import_rows
from .indices import build_tracker_record, write_outputs


def _cmd_usecase_validate(args) -> int:
    record = load_record(args.file)
    problems = validate_record(record, args.schema)
    if problems:
        for p in problems:
            print(f"FAIL - {args.file}: {p}", file=sys.stderr)
        return 1
    print(f"ok - {args.file} ({record.get('id')})")
    return 0


def _cmd_usecase_list(args) -> int:
    records = load_registry_dir(args.registry)
    for r in records:
        print(f"{r['id']}  {r['lifecycle']:<14} {r['risk_tier']:<6} {r['title']}")
    print(f"-- {len(records)} use case(s)", file=sys.stderr)
    return 0


def _cmd_usecase_new(args) -> int:
    from .registry import scaffold
    rec = scaffold(args.id, args.title, args.owner, args.risk_tier)
    out = Path(args.out)
    if out.suffix not in (".yaml", ".yml", ".json"):
        raise MamaToolsError("output path must be .yaml/.yml or .json")
    if out.exists():
        raise MamaToolsError(f"refusing to overwrite existing file: {out}")
    if out.suffix == ".json":
        out.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    else:
        import yaml
        out.write_text(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"wrote {out} ({rec['id']}) — fill in intended_decision_use, domains, and baselines, then re-validate")
    return 0


def _cmd_metric_calc(args) -> int:
    inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    result = calculate(args.card, inputs, label=args.label)
    print(json.dumps(result, indent=2))
    return 0


def _cmd_metric_cards(args) -> int:
    print("\n".join(sorted(RATIO_CARDS)))
    print(f"-- {len(RATIO_CARDS)} calculable ratio cards (others: calculate in your own tooling)", file=sys.stderr)
    return 0


def _cmd_metrics_import(args) -> int:
    ids = {r["id"] for r in load_registry_dir(args.registry)}
    rows = import_rows(args.file, registry_ids=ids)
    written = append_series(args.series_dir, rows)
    print(f"imported {written} row(s) into {args.series_dir} (append-only)")
    return 0


def _cmd_tracker_generate(args) -> int:
    records = load_registry_dir(args.registry)
    ledger = None
    if args.ledger:
        try:
            from mama_integrations.ledger import load_ledger  # type: ignore
        except ImportError as exc:
            raise MamaToolsError(
                "mama-integrations is not installed — install with the [autonomy] extra "
                "to compute the autonomy axis (it must flow through the controlled import, never a spreadsheet)"
            ) from exc
        ledger = load_ledger(args.ledger)
    trackers = [build_tracker_record(r, args.series_dir, ledger) for r in records]
    paths = write_outputs(args.out, trackers)
    for t in trackers:
        a = t["axes"]
        print(f"{t['usecase_id']}: automation={a['automation'] and a['automation']['value']} "
              f"autonomy={a['autonomy'] and a['autonomy']['index']} (floor L{(a['autonomy'] or {}).get('min_level', 'n/a')}) "
              f"value={a['value'] and a['value']['value']}")
    for n in [n for t in trackers for n in t.get("notes", [])]:
        print(f"note: {n}", file=sys.stderr)
    print(f"wrote: " + ", ".join(paths.values()))
    return 0


def _cmd_portfolio(args) -> int:
    ledger = None
    if args.ledger:
        try:
            from mama_integrations.ledger import load_ledger  # type: ignore
        except ImportError as exc:
            raise MamaToolsError(
                "mama-integrations is not installed — install with the [autonomy] extra "
                "(pip install mama-tools[autonomy]) to display autonomy profiles"
            ) from exc
        ledger = load_ledger(args.ledger)
    print(build_view(args.registry, ledger))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mama-tools",
        description=(
            "MAMA reference tooling: use-case registry, metric calculation, and a "
            "side-by-side portfolio view that never blends measures (ADR-003). "
            "Local-first and offline."
        ),
    )
    parser.add_argument("--version", action="version", version=f"mama-tools {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("usecase", help="use-case registry operations")
    usub = p.add_subparsers(dest="ucmd", required=True)
    v = usub.add_parser("validate", help="validate a use-case record")
    v.add_argument("file")
    v.add_argument("--schema", help="override the bundled usecase-record schema")
    v.set_defaults(func=_cmd_usecase_validate)
    l = usub.add_parser("list", help="list validated use cases in a registry directory")
    l.add_argument("registry")
    l.set_defaults(func=_cmd_usecase_list)
    n = usub.add_parser("new", help="scaffold a starter use-case record (validated before written)")
    n.add_argument("--id", required=True, help="usecase-<slug> (lowercase, hyphenated)")
    n.add_argument("--title", required=True)
    n.add_argument("--owner", required=True)
    n.add_argument("--risk-tier", default="medium", choices=["low", "medium", "high"])
    n.add_argument("--out", required=True, help="output path (.yaml recommended)")
    n.set_defaults(func=_cmd_usecase_new)

    p = sub.add_parser("metric", help="metric calculation")
    msub = p.add_subparsers(dest="mcmd", required=True)
    c = msub.add_parser("calc", help="calculate one ratio metric from an inputs JSON file")
    c.add_argument("card", help="card id (see: mama-tools metric cards)")
    c.add_argument("inputs", help="inputs JSON: numerator, denominator, card_version, window")
    c.add_argument("--label", default="observed", choices=["observed", "estimate", "forecast"])
    c.set_defaults(func=_cmd_metric_calc)
    cards = msub.add_parser("cards", help="list cards with registered calculators")
    cards.set_defaults(func=_cmd_metric_cards)

    p = sub.add_parser("metrics", help="series import (the seam to your own measurement systems)")
    msub2 = p.add_subparsers(dest="scmd", required=True)
    im = msub2.add_parser("import", help="import observations from CSV/JSON (card-versioned, labeled, append-only)")
    im.add_argument("file", help="CSV with columns usecase_id,card_id,card_version,window,value,label[,source_note] or JSON {rows: [...]}")
    im.add_argument("--registry", required=True, help="registry directory (linkage must be explicit; no orphans)")
    im.add_argument("--series-dir", required=True, help="directory for per-use-case series files (JSONL, append-only)")
    im.set_defaults(func=_cmd_metrics_import)

    p = sub.add_parser("tracker", help="per-axis indices + multi-dimensional tracker (never a composite)")
    tsub = p.add_subparsers(dest="tcmd", required=True)
    tc = tsub.add_parser("generate", help="compute tracker records and render plot + report")
    tc.add_argument("--registry", required=True)
    tc.add_argument("--series-dir", help="series directory from 'metrics import'")
    tc.add_argument("--ledger", help="mama autonomy ledger YAML (requires mama-tools[autonomy])")
    tc.add_argument("--out", required=True, help="output directory (tracker.jsonl, tracker-report.md, tracker-plot.svg)")
    tc.set_defaults(func=_cmd_tracker_generate)

    p = sub.add_parser("portfolio", help="side-by-side portfolio view (never blended)")
    p.add_argument("registry", help="directory of use-case records")
    p.add_argument("--ledger", help="mama autonomy ledger YAML (requires mama-tools[autonomy])")
    p.set_defaults(func=_cmd_portfolio)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MamaToolsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
