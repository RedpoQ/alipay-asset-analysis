# Asset Analysis

Current release: `v0.1.0-local`

`asset_analysis` is a local Alipay fund analysis assistant for daily personal use. It imports local holdings, runs deterministic rule-based analysis, writes local reports, and produces a short Hermes/WeChat-friendly summary.

It is not a trading bot. It does not do automatic trading, backtesting, or prediction.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m asset_analysis.onboarding.init_project
.\scripts\daily_run.ps1
```

Detailed setup is in [docs/QUICK_START.md](docs/QUICK_START.md).

## Daily Usage

- Keep your local inputs under `private/`
- Validate setup with `python -m asset_analysis.ux.setup_check --config private/config.local.yaml`
- Run the daily workflow with `.\scripts\daily_run.ps1`
- Read `reports/private/latest/chat_summary.txt`

## Safety Boundary

- `signal_engine` is the sole decision source for `add`, `reduce`, and `hold`
- no automatic trading
- no prediction
- no network or API keys required for the default local flow
- private holdings should stay under `private/`
- demo export is sanitized, but still needs human review before sharing

## Docs

- [Quick Start](docs/QUICK_START.md)
- [Daily Workflow](docs/DAILY_WORKFLOW.md)
- [Hermes Integration](docs/HERMES_INTEGRATION.md)
- [Config Reference](docs/CONFIG_REFERENCE.md)
- [Privacy And Safety](docs/PRIVACY_AND_SAFETY.md)
- [Module Index](docs/MODULE_INDEX.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Release Notes](RELEASE_NOTES_v0.1.0-local.md)
- [Changelog](CHANGELOG.md)
