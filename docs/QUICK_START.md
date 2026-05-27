# Quick Start

Current release: `v0.1.0-local`

This project is a local Alipay fund analysis assistant. It runs offline by default, does not require API keys, and keeps the signal decision path rule-based.

## Commands

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Initialize local files:

```powershell
python -m asset_analysis.onboarding.init_project
```

Preview the Alipay CSV before conversion:

```powershell
python -m asset_analysis.alipay.preview --input private/alipay_holdings.local.csv
```

Run setup validation:

```powershell
python -m asset_analysis.ux.setup_check --config private/config.local.yaml
```

Run the daily workflow:

```powershell
.\scripts\daily_run.ps1
```

Read the generated Hermes/WeChat summary:

```powershell
Get-Content reports\private\latest\chat_summary.txt
```

Run the release gate:

```powershell
python -m asset_analysis.release.gate --output reports/release_gate --skip-tests
```

## Notes

- Keep real holdings and quotes under `private/`.
- Review `reports/private/latest/` after each run.
- For a deeper walkthrough, see [DAILY_WORKFLOW.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/docs/DAILY_WORKFLOW.md).
