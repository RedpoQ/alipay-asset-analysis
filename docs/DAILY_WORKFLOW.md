# Daily Workflow

## Private Inputs

- `private/alipay_holdings.local.csv`: your local Alipay holdings export.
- `private/holdings.local.yaml`: normalized holdings file produced or consumed by the workflow.
- `private/manual_quotes.local.csv`: optional manual NAV or price input when `analysis.data_source: manual`.

These files are local-only and should stay out of git.

## `config.local.yaml`

The main workflow entrypoint is `private/config.local.yaml`. It controls:

- input mode and file paths
- output directories
- data source and rules
- notification dry-run behavior
- preflight thresholds
- history and chat summary generation

Start from `private/config.local.example.yaml`, then keep local edits in `private/config.local.yaml`.

## Manual Quotes

If you want user-supplied quotes instead of mock data:

- set `analysis.data_source: manual`
- set `analysis.quotes: private/manual_quotes.local.csv`

Manual quotes are local facts, not predictions. Missing or stale rows are surfaced by preflight and data quality output.

## Preflight

Run before the full workflow when you want a fast validation pass:

```powershell
python -m asset_analysis.ux.setup_check --config private/config.local.yaml
```

Preflight checks local files, input mode, quote freshness, and duplicate or missing data conditions before report generation.

## Pipeline

The normal daily command is:

```powershell
.\scripts\daily_run.ps1
```

This wraps the existing daily workflow and keeps the project’s current command surface stable.

## Chat Summary

After a successful run, read:

- `reports/private/latest/chat_summary.txt`

That file is the short deterministic output intended for Hermes or WeChat copy/paste. It is derived from `report.json`; it does not create new signals.

## History

When history is enabled, the workflow updates:

- `reports/history_index.json`
- `reports/trend/`
- dated runs under `reports/daily/YYYY-MM-DD/`

This is for local trend tracking, not backtesting.

## Latest Output Directory

The latest pointer directory is:

- `reports/private/latest/`

Typical files:

- `report.json`
- `report.md`
- `chat_summary.txt`
- `preflight_report.json`
- `effective_config.json`

## Troubleshooting

- Missing local templates: run `python -m asset_analysis.onboarding.init_project`
- Bad Alipay headers: run `python -m asset_analysis.alipay.preview --input private/alipay_holdings.local.csv`
- Config path issues: run `python -m asset_analysis.ux.setup_check --config private/config.local.yaml`
- Manual quote mismatch: verify `private/manual_quotes.local.csv` and `analysis.quotes`
- Release validation: run `python -m asset_analysis.release.gate --output reports/release_gate --skip-tests`
