# Hermes Daily Fund Analysis Failure Prompt

When the Hermes daily fund workflow fails:

- do not invent today’s fund analysis
- read error output, `preflight_report.json`, or setup-check style output
- explain the exact failure stage
- give one concrete fix command

Failure-stage guidance:
- `setup_check`: config path missing, private files missing, or local templates not initialized
- `preflight`: input files exist but checks failed before pipeline completion
- `conversion`: Alipay CSV could not be normalized into standard holdings
- `manual quotes`: manual quote file missing, stale, or malformed
- `pipeline`: workflow reached pipeline/report generation and failed there
- `chat_summary`: report generation succeeded but `chat_summary.txt` was missing or unreadable

Safety rules:
- do not predict prices
- do not override signals
- do not recommend automatic trading
