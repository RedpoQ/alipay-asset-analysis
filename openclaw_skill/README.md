# OpenClaw Asset Analysis Skill

这是一个最小通用的 OpenClaw skill wrapper，用于调用现有 `asset_analysis` pipeline。

当前工作区没有现成的 OpenClaw manifest 约定，因此这里提供的是可适配模板：
- 入口：[asset_analysis_skill.py](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/openclaw_skill/asset_analysis_skill.py)
- manifest：[skill.json](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/openclaw_skill/skill.json)

默认行为：
- `data_source="mock"`
- `reporter="offline"`

说明：
- OpenClaw wrapper 只负责调用 pipeline
- `signal_engine` 仍然是唯一的 `add/reduce/hold` 决策源
- 不包含 Hermes 调度
- 不包含推送通知
- 不包含自动交易
