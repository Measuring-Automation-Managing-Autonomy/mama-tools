# mama-tools

**MAMA** (Measuring Automation & Measuring Autonomy) reference tooling: a
**use-case registry**, **metric calculation/validation**, and a
**side-by-side portfolio view** that displays automation measures, `mama`
autonomy profiles, and practice profiles **without ever blending them**
(mama-framework [ADR-003](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/decisions/adr-003-no-composite-score.md)).

> **First reference:** MAMA (Measuring Automation & Measuring Autonomy) uses
> the `mama` (measuring and managing autonomy) method for its
> autonomy-governance component. The `mama` method's canonical home is
> [`emmanuel-a-otchere/measuring-and-managing-autonomy`](https://github.com/emmanuel-a-otchere/measuring-and-managing-autonomy).

**Status:** `draft` (v0.1.0) · **License:** Apache-2.0 · **Maintainer:** see [MAINTAINERS.md](MAINTAINERS.md)

## Install

```bash
pip install git+https://github.com/Measuring-Automation-Managing-Autonomy/mama-tools.git@v0.1.0
# with the autonomy display path (version-pinned adapter for upstream mama outputs):
pip install "mama-tools[autonomy] @ git+https://github.com/Measuring-Automation-Managing-Autonomy/mama-tools.git@v0.1.0"
```

Local-first and offline: every command reads and writes files you own;
nothing is sent anywhere. No telemetry.

## Commands

```bash
mama-tools usecase validate examples/usecase-refunds-agent.yaml   # schema + cross-checks
mama-tools usecase list examples/registry/                        # validated listing
mama-tools metric cards                                           # cards with registered calculators
mama-tools metric calc exception-rate examples/metric-inputs.json # honest ratio arithmetic
mama-tools portfolio examples/registry/ --ledger ledger.yaml      # side-by-side view
mama-tools metrics import examples/series.csv --registry examples/registry --series-dir series/
mama-tools tracker generate --registry examples/registry --series-dir series/ --ledger ledger.yaml --out tracker/
```

## Design rules

1. **Never blended.** Automation metrics, `mama` autonomy profiles, and
   practice profiles are separate instruments in separate columns/records;
   there is no composite and no join beyond the use-case ID
   ([ADR-003](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/decisions/adr-003-no-composite-score.md)).
2. **Autonomy is pass-through.** Autonomy values come from upstream `mama`
   outputs imported **as issued** via
   [mama-integrations](https://github.com/Measuring-Automation-Managing-Autonomy/mama-integrations)
   (optional `[autonomy]` extra) — this tool never recomputes, renames, or
   rescales them.
3. **No guessed formulas.** Metric cards define formulas as prose. The
   calculator implements explicit, tested arithmetic for a fixed set of
   ratio cards (`mama-tools metric cards`); anything else must be computed
   in your own tooling and recorded as a baseline — mama-tools refuses to
   guess.
4. **Labels travel.** Every baseline carries `observed`/`estimate`/`forecast`
   and the card version; comparability exists only within a card version.
5. **The tracker is per-axis, never a composite.** The [tracker](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/indices-and-tracking.md) plots three separate indices - Automation (automation-coverage card value), Autonomy (mean granted level x20 from the ledger **as issued**, with the minimum granted level as a mandatory floor), and Value Realization (realized-vs-forecast, unclamped) - as an SVG trajectory + Markdown report. Axes are never summed, averaged, or weighted together ([ADR-005](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/decisions/adr-005-display-indices-and-tracker.md)).
6. **The autonomy axis has no CSV seam.** Metric observations flow in through the flat [series interface](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/indices-and-tracking.md#4-the-series-interface-pulling-the-actual-numbers) (`metrics import`); delegated-authority numbers flow only through the version-gated `mama-integrations` import.
7. **Evidence-gated practice profiles.** A practice-maturity stage ≥ 2
   without evidence references is rejected at validation (recorded as the
   stage below, per the [maturity model](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/maturity-model.md)).

## Threat review (summary)

- **Input surface:** YAML/JSON files you point it at. Parsing uses
  `yaml.safe_load`; JSON via stdlib. No code execution from data.
- **No network.** No downloads, no telemetry, no outbound calls at runtime
  (the `[autonomy]` extra is installed by *you*, like any dependency).
- **Path/ID hygiene:** use-case IDs are slug-validated; nothing executes
  from record content; errors fail closed with typed exceptions.
- **Trust boundaries:** the tool displays governance data — it does not
  authorize anything, and its output is not a control. Keep the records
  under the same access control as the evidence they reference.

## Status

`draft` (v0.1.0). Part of the [MAMA framework](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework) —
see the [charter](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/charter.md)
and [limitations](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/charter.md#5-limitations).
Pilot-stage until the multi-organization pilot reports.
