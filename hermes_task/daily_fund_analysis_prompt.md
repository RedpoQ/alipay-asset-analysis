# Hermes Daily Fund Analysis Prompt

Run the configured daily command for the local `asset_analysis` project.

Required behavior:
- Run `.\\scripts\\daily_run.ps1` or `python -m asset_analysis.workflow.daily_run --config private/config.local.yaml --json-only`
- Read `reports/private/latest/chat_summary.txt`
- return the text mostly as-is
- if the summary is too long, compress it without changing meaning
- read chat_summary.txt before looking at any optional JSON files
- mention that the report is rule-driven and not price prediction

Safety rules:
- do not override signals
- do not predict market direction
- do not generate new add/reduce/hold
- do not add new fund recommendations
- do not send holdings to an LLM by default
- do not write manual analysis when the workflow already produced `chat_summary.txt`

If the command fails:
- switch to `daily_fund_analysis_failure_prompt.md`
