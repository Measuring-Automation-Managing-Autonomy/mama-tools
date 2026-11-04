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


def _cmd_metric_calc(args) -> int:
    inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    result = calculate(args.card, inputs, label=args.label)
    print(json.dumps(result, indent=2))
    return 0


def _cmd_metric_cards(args) -> int:
    print("\n".join(sorted(RATIO_CARDS)))
    print(f"-- {len(RATIO_CARDS)} calculable ratio cards (others: calculate in your own tooling)", file=sys.stderr)
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

    p = sub.add_parser("metric", help="metric calculation")
    msub = p.add_subparsers(dest="mcmd", required=True)
    c = msub.add_parser("calc", help="calculate one ratio metric from an inputs JSON file")
    c.add_argument("card", help="card id (see: mama-tools metric cards)")
    c.add_argument("inputs", help="inputs JSON: numerator, denominator, card_version, window")
    c.add_argument("--label", default="observed", choices=["observed", "estimate", "forecast"])
    c.set_defaults(func=_cmd_metric_calc)
    cards = msub.add_parser("cards", help="list cards with registered calculators")
    cards.set_defaults(func=_cmd_metric_cards)

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
