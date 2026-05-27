# Changelog

## v0.1.0-local

- established a local Alipay fund workflow centered on `private/` inputs and daily reports
- kept fund signals deterministic through the rule engine and existing `signal_engine`
- added manual quote support for offline or user-supplied daily data
- added preflight checks for config, holdings, duplicate codes, and quote freshness
- added Hermes-friendly chat summary output for local automation and WeChat copy/paste
- added sanitized public demo export for safer sharing
- added a release gate for closeout validation and local release packaging
