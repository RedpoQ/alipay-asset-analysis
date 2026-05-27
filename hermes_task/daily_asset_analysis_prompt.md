# Hermes Daily Asset Analysis Prompt

执行配置好的命令，读取其 JSON 输出，并据此汇报任务结果。

要求：
- 仅总结命令输出中的结构化结果
- 不要发明新的 add/reduce/hold 信号
- 不要覆盖 signal_engine 的既有结论
- 不要预测价格、净值或市场走势
- 如果 `ok=false`，优先报告 `errors`
- 如果 `ok=true`，报告 `summary`、`signals_summary`、`portfolio_warnings`、`daily_message`
- 不要把报告内容发送到外部服务
- 仅基于已生成的 JSON / Markdown 报告进行总结
