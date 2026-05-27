# Hermes Task Template

这里提供一个最小通用的 Hermes 任务模板，用于定时调用现有 `asset_analysis` 适配器。

文件：
- [daily_asset_analysis_task.example.yaml](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_asset_analysis_task.example.yaml)
- [daily_asset_analysis_prompt.md](C:/Users/20634/Documents/openclaw与hermes_支付宝基金_skill/hermes_task/daily_asset_analysis_prompt.md)

说明：
- 当前不依赖具体 Hermes runtime internals
- Hermes 只负责调度和调用
- `signal_engine` 仍然是唯一的信号决策源
- 不包含推送通知
- 不包含自动交易
- 不包含后台服务实现
