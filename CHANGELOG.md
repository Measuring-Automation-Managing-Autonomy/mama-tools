# Changelog — mama-tools

Versions are semver; `draft`-status artifacts may change without notice.

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
