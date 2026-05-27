# Config Reference

The daily workflow config is usually `private/config.local.yaml`. The example baseline is `private/config.local.example.yaml`.

## `profile`

- `name`: built-in profile name such as `balanced`
- `file`: optional profile YAML path such as `examples/profiles/balanced.profile.yaml`

Profiles provide defaults. Explicit local config values still win.

## `input`

- `mode`: `alipay_csv` or `holdings_yaml`
- `alipay_csv`: path to the local Alipay export
- `holdings_yaml`: path to the normalized holdings file

## `analysis`

- `data_source`: usually `mock` or `manual`
- `reporter`: keep `offline` for local-safe default behavior
- `rules`: rule file path
- `asset_groups`: group definition path
- `portfolio_template`: portfolio structure path
- `overseas_exposure`: QDII and overlap exposure config path
- `quotes`: manual quotes file path

## `preflight`

- `enabled`: turn preflight on or off
- `strict_quotes`: missing manual quotes become critical failures when true
- `fail_on_stale_quotes`: stale quotes can block the run when true
- `fail_on_duplicate_codes`: duplicate holding codes can block the run when true
- `max_normal_stale_days`: stale threshold for normal assets
- `max_qdii_stale_days`: stale threshold for QDII assets

## `notification`

- `enabled`: enable notification orchestration
- `config`: channel config file
- `dry_run`: keep true unless you intentionally want real delivery

Push is off by default in the local example flow.

## `chat_summary`

- `enabled`: generate short Hermes/WeChat output
- `style`: summary style such as `wechat`
- `max_signals`: cap the displayed signals
- `max_warnings`: cap the displayed warnings

## `history`

- `enabled`: write dated runs and history outputs
- `reports_dir`: base directory for dated reports
- `index_path`: history index JSON path
- `trend_output_dir`: trend markdown output directory

## Manual Quotes

Manual quote usage is controlled by:

- `analysis.data_source: manual`
- `analysis.quotes: private/manual_quotes.local.csv`

This keeps daily use local and deterministic without requiring network access.

## Exposure Config

The exposure layer is controlled by:

- `analysis.overseas_exposure`
- `analysis.asset_groups`
- `analysis.portfolio_template`

These files support structural overlap and QDII analysis. They do not introduce prediction and do not replace `signal_engine`.
