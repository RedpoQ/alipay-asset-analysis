# Asset Analysis

当前版本：`v0.2.0`

`asset_analysis` 是一个面向个人日常使用的本地基金/资产分析工具，当前重点适配单渠道的支付宝基金持仓场景。

它的目标不是预测涨跌，而是把本地持仓、目标仓位、规则检查、组合结构分析、风险提醒、聊天摘要整理成一套可重复执行的离线工作流，方便每天快速查看组合状态，并生成适合 Hermes / 微信阅读的简短摘要。

## 项目定位

这个项目更适合：

- 希望做本地、可控、可解释的日常基金检查
- 希望把持仓分析结果整理成适合 Hermes / 微信阅读的摘要
- 希望把仓位偏离、集中度风险、QDII 曝险等检查固定成日常流程

这个项目不适合：

- 自动交易
- 价格预测
- 回测系统
- 机构级实时量化行情系统

## 核心边界

- `signal_engine` 是唯一的 `add` / `reduce` / `hold` 信号来源
- LLM 只允许解释已有结果，不允许生成或覆盖信号
- OpenClaw 只负责包装和调用 pipeline
- Hermes 只负责调度、读取输出和生成摘要
- 通知层只消费 `report.json` / `report.md`
- 历史层只读取既有 `report.json`
- 不做自动交易
- 不做价格预测
- 不构成投资建议

## 当前能力

项目当前支持：

- 支付宝持仓 CSV / JSON 转换
- 本地持仓 YAML 分析
- `mock / manual / public_fund / auto` 数据源
- 手工净值 `manual quotes`
- 确定性的规则引擎
- 离线报告、聊天摘要和中文本地化文案
- OpenClaw / Hermes 适配
- 组合分组分析
- QDII / 海外曝险与重叠提示
- preflight 数据检查
- release gate 安全检查
- **基金申购状态检查**（暂停申购/限购/大额限制）

## 日常使用：3 个命令

1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

2. 初始化本地模板

```bash
python -m asset_analysis.onboarding.init_project
```

3. 运行每日流程

```bash
# Linux/macOS
./scripts/daily_run.sh

# Windows
.\scripts\daily_run.ps1
```

详细初始化步骤见 [docs/QUICK_START.md](docs/QUICK_START.md)。

## 单渠道支付宝工作流

推荐的单渠道日常流程：

1. 把真实持仓放在 `private/`
2. 用 `setup_check` 检查本地配置
3. 用 `daily_run` 生成日报
4. 查看 `chat_summary.txt`
5. 如需要，再粘贴到 Hermes / 微信

常用命令：

```bash
python -m asset_analysis.ux.setup_check --config private/config.local.yaml
python -m asset_analysis.workflow.daily_run --config private/config.local.yaml
```

最常看的输出：

- `reports/private/latest/report.json`
- `reports/private/latest/report.md`
- `reports/private/latest/chat_summary.txt`
- `reports/private/latest/preflight_report.md`

## Hermes 最小联调命令

如果你只是想快速验证 Hermes 接入，建议先跑最小离线链路：

```bash
python -m asset_analysis.hermes_adapter --holdings examples/real_existing_holdings.yaml --output reports/hermes_daily --data-source mock --reporter offline
```

预期输出：

- `reports/hermes_daily/report.json`
- `reports/hermes_daily/report.md`
- `reports/hermes_daily/run.json`

如果还要生成聊天摘要：

```bash
python -m asset_analysis.chat_summary.cli --report reports/hermes_daily/report.json --output reports/hermes_daily/chat_summary.txt --json-output reports/hermes_daily/chat_summary.json
```

## 基金申购状态检查

新增功能：自动检查持仓基金的申购状态，包括：

- 开放申购
- 暂停申购
- 限制大额申购
- 限制申购

### 使用方式

申购状态检查已集成到 `hermes_adapter.py`，运行分析时会自动检查：

```bash
python -m asset_analysis.hermes_adapter --holdings your_holdings.yaml --output reports/hermes_daily --data-source mock
```

输出示例：

```
申购状态摘要：
000834: 申购✅ 开放申购 | 赎回✅ 开放赎回
006075: 申购❌ 暂停申购 | 赎回✅ 开放赎回
021277: 申购✅ 限制大额申购 | 赎回✅ 开放赎回
  限制: 限制大额申购
```

### 独立使用

也可以单独检查基金申购状态：

```python
from asset_analysis.fund_purchase_status import check_fund_purchase_status

status = check_fund_purchase_status("000834")
print(f"{status.code}: {status.purchase_status}")
print(f"可申购: {status.is_purchase_allowed}")
```

### 数据来源

使用东方财富基金API获取申购状态数据，无需API key。

## 数据源说明

### `mock`

- 默认最安全
- 不需要外网
- 适合流程联调和结构检查
- 不代表真实净值

### `manual`

- 适合真实本地日常使用
- 使用你自己维护的净值 / 价格文件
- 不代表实时行情
- 会做新鲜度检查、缺失检查和对齐检查

### `public_fund` / `auto`

- 可作为补充参考
- 可能受外部数据质量和可用性影响
- 不应默认作为最稳日常路径

## 隐私与安全

- 真实持仓应放在 `private/`
- 不要提交真实 `private/*.csv`、`private/*.yaml`、`private/*.json`
- 只提交 `.example` 模板文件
- 默认流程不需要 API key
- 默认不启用真实推送
- 默认 `reporter` 为 `offline`
- 默认推荐先用 `mock` 或 `manual`

即使项目带有 demo / export 能力，对外分享前仍应人工检查输出内容。

## 对外共享前建议

在公开分享或发给别人测试前，建议先运行：

```bash
python -m asset_analysis.release.gate --output reports/release_gate --skip-tests
```

它会检查：

- 必需文件是否齐全
- `.gitignore` 隐私规则是否正确
- 默认安全配置是否符合预期
- pipeline / Hermes / chat summary / preflight 等 smoke 路径是否可运行

## 目录说明

- `asset_analysis/`：核心代码
- `examples/`：公开样例和模板
- `private/`：本地私有输入模板
- `scripts/`：日常运行脚本
- `hermes_task/`：Hermes 任务模板
- `openclaw_skill/`：OpenClaw skill 包装
- `docs/`：补充文档

## 文档导航

- [Quick Start](docs/QUICK_START.md)
- [Daily Workflow](docs/DAILY_WORKFLOW.md)
- [Hermes Integration](docs/HERMES_INTEGRATION.md)
- [Config Reference](docs/CONFIG_REFERENCE.md)
- [Privacy And Safety](docs/PRIVACY_AND_SAFETY.md)
- [Module Index](docs/MODULE_INDEX.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Release Notes](RELEASE_NOTES_v0.1.0-local.md)
- [Changelog](CHANGELOG.md)

## 限制说明

- 这是本地规则驱动工具，不是投资顾问
- 不做价格预测
- 不做自动交易
- 不做回测
- 海外/QDII 分析主要基于规则和关键词，不是穿透式底层持仓分析
- 手工净值完全依赖用户维护
- 未匹配到的本地化文案会安全回退到原始文本
