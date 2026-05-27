# Release Notes: v0.1.0-local

## Purpose

`v0.1.0-local` packages the project as a local Alipay fund analysis assistant for daily personal use. The emphasis is offline operation, deterministic signals, and safer handling of private holdings.

## Highlights

- Alipay holdings import and CSV preview
- deterministic rule engine with existing `signal_engine` as the decision source
- manual quotes for local daily use
- preflight validation before daily execution
- Hermes and WeChat friendly `chat_summary.txt`
- sanitized public demo export
- release gate for documentation, safety, and workflow validation

## Core Commands

```powershell
python -m asset_analysis.onboarding.init_project
python -m asset_analysis.ux.setup_check --config private/config.local.yaml
.\scripts\daily_run.ps1
python -m asset_analysis.release.gate --output reports/release_gate --skip-tests
```

## Safety Boundaries

- no automatic trading
- no prediction
- no backtesting
- no network requirement for the default local workflow
- no API keys required for the default local workflow
- `signal_engine` remains the only source of `add/reduce/hold`

## Known Limitations

- single local-user workflow
- manual quotes are user-supplied and may be stale
- public demo export still needs human review
- Hermes templates may need runtime-specific adjustment
- no real push by default

## Disclaimer

This project is not investment advice. It is a local analysis assistant with deterministic rules and explicit safety boundaries.
