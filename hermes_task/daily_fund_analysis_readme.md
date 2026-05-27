# Hermes Daily Fund Analysis Cronjob

This template makes Hermes run the existing local daily workflow and then read `reports/private/latest/chat_summary.txt`.

Key rule:
- Hermes must not analyze funds directly.

Use:
- Cronjob template: [daily_fund_analysis.cronjob.example.yaml](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis.cronjob.example.yaml)
- Success prompt: [daily_fund_analysis_prompt.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis_prompt.md)
- Failure prompt: [daily_fund_analysis_failure_prompt.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_fund_analysis_failure_prompt.md)

Expected command:
- `.\\scripts\\daily_run.ps1`

Expected output:
- `reports/private/latest/chat_summary.txt`
- `reports/private/latest/report.json`
- `reports/private/latest/preflight_report.json`

Failure handling:
- Do not generate fund analysis manually.
- Read structured errors.
- Tell the user which config or file failed.
- Provide one concrete repair command.

Limitations:
- The YAML schema may need runtime-specific adjustment for a real Hermes scheduler.
- No automatic trading.
- No market prediction.
- Hermes only reads the generated summary and related structured outputs.
