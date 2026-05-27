# Hermes Integration

## Core Rule

Hermes must not analyze funds directly.

Hermes is a runner and reader for this local project. The fund analysis must come from the existing local workflow and the deterministic `signal_engine`.

## What Hermes Should Run

Preferred commands:

```powershell
python -m asset_analysis.hermes.cronjob_runner --config private/config.local.yaml
```

or:

```powershell
.\scripts\daily_run.ps1
```

Hermes should run one of those commands, then read:

- `reports/private/latest/chat_summary.txt`

## What Hermes Should Read

Primary output:

- `reports/private/latest/chat_summary.txt`

Related structured outputs:

- `reports/private/latest/report.json`
- `reports/private/latest/preflight_report.json`

Hermes should return the generated summary, not invent a fresh narrative from raw holdings.

## Prompt Template Location

Existing templates live under `hermes_task/`:

- [daily_fund_analysis.cronjob.example.yaml](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis.cronjob.example.yaml)
- [daily_fund_analysis_prompt.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis_prompt.md)
- [daily_fund_analysis_failure_prompt.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis_failure_prompt.md)
- [daily_fund_analysis_readme.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis_readme.md)

## Failure Behavior

If the workflow succeeds:

- return `chat_summary.txt`
- include the latest output path if useful

If the workflow fails:

- do not generate manual fund analysis
- read the structured failure output
- explain which stage failed
- provide one concrete repair command

Useful repair commands:

- `python -m asset_analysis.onboarding.init_project`
- `python -m asset_analysis.ux.setup_check --config private/config.local.yaml`
- `python -m asset_analysis.alipay.preview --input private/alipay_holdings.local.csv`

## Safety Boundaries

- Hermes does not override `signal_engine`.
- Hermes does not create `add/reduce/hold` signals.
- Hermes does not do prediction.
- Hermes does not do automatic trading.
- Hermes should not expose raw private holdings in chat responses.
