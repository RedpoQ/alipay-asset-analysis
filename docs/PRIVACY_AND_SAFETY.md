# Privacy And Safety

## Local Privacy Boundary

- `private/` is local-only input space and is protected by `.gitignore`.
- `reports/private/` and `reports/daily/` are ignored by `.gitignore`.
- Real holdings, local quote files, and local config files should stay under `private/`.

## Demo Export

The demo export under `reports/demo/` is sanitized for safer sharing, but it still requires human review before publication.

Sanitization reduces exposure risk. It is not a guarantee that every context-specific private detail is safe to publish.

## LLM And Push Defaults

- LLM is off by default in the local example flow.
- Push is off by default.
- The recommended local path is offline and deterministic.

## Hard Safety Limits

- no automatic trading
- no prediction
- no backtesting
- no API-key requirement for the default local workflow

## Decision Boundary

`signal_engine` is the sole decision source for `add`, `reduce`, and `hold`.

That means:

- Hermes does not generate signals
- chat summary does not generate signals
- notification layers do not generate signals
- docs and demo export do not generate signals

The project is an analysis assistant, not an execution system and not investment advice.
