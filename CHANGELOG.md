# Changelog — mama-tools

Versions are semver; `draft`-status artifacts may change without notice.

## [0.3.0] — 2026-11-05

### Added (indices and tracking, per mama-framework ADR-005)

- **Series interface**: `metrics import` ingests card-versioned, labeled observations (CSV or JSON) into append-only per-use-case series files - the seam to an organization's own measurement systems; registry linkage is explicit (orphans rejected)
- **Per-axis display indices + tracker**: `tracker generate` computes the Automation Index (automation-coverage card value), the Autonomy Index (mean granted level x20 from the ledger **as issued**, floor = min granted level mandatory and rendered), and Value Realization (realized-vs-forecast, unclamped) into versioned tracker records (`schemas/tracker-record.schema.json`), an SVG trajectory plot, and a Markdown report - with the no-composite rule burned into every artifact and a Submarine Line narrative rule when any linked domain holds level 0
- Schemas: `series-record.schema.json`, `tracker-record.schema.json`
- Autonomy inputs flow through the `mama-integrations` `LedgerImportResult` (importer warnings surfaced in the report); no recomputation of upstream scores anywhere

## [0.1.0] — 2026-11-05

### Added (initial release, CR MAMA-ORG-CR-001 Phase 3)

- Use-case registry: schema-validated records joining automation baselines,
  practice profiles, value hypotheses, evidence, and owned decisions
  (`schemas/usecase-record.schema.json`)
- Metric calculator with an explicit, tested registry of ratio cards and a
  refusal to guess formulas; labels (observed/estimate/forecast) and card
  versions required
- Portfolio view: side-by-side display of automation measures, practice
  profiles, and — via the optional `mama-integrations` adapter — upstream
  `mama` autonomy profiles exactly as issued; never blended (ADR-003)
- CLI (`mama-tools`), worked examples, CI (pytest 3.10/3.12/3.13 + example
  validation)
