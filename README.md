
# 🐼 Sichuan Air Quality & Traffic Bot (四川空气质量与限行助手)

这是一个专为**四川地区**设计的自动化空气质量监测与限行提醒工具。它能自动获取四川省内城市的实时 AQI、未来 7 天天气趋势，并根据成都最新的重污染天气预警政策，通过微信推送详细的限行指令。

## 🌟 核心功能

* **实时数据分析**：自动对接四川省生态环境厅数据源，获取最准确的实况 AQI 及首要污染物。
* **7 天趋势预测**：清晰展示未来一周的空气质量变化，并标注对应的**星期**和**预警等级**。
* **智能限行计算**：
* **常规模式**：自动识别工作日尾号限行（07:30 - 20:00）。
* **预警模式**：支持**黄色/橙色预警**自动切换，明确提示 **06:00 - 22:00** 限行时段及小客车、货车限制。
* **节假日识别**：内置 `chinese_calendar`，自动跳过法定节假日和周末。


* **全自动运行**：完美支持 GitHub Actions，每日零成本自动运行并推送。

## 🚀 快速开始

### 1. 准备工作

* 拥有一个 GitHub 账号。
* 访问 [Server酱 (SCT)](https://sct.ftqq.com/) 获取你的 `SendKey`（用于微信推送）。

### 2. 部署步骤

1. **Fork 本仓库** 到你自己的 GitHub 账号下。
2. **配置 Secret（重要）**：
* 进入你 Fork 后的仓库，点击 `Settings` -> `Secrets and variables` -> `Actions`。
* 点击 `New repository secret`。
* Name 填入：`SEND_KEY`。
* Value 填入：你的 Server酱 SendKey。


3. **开启自动化流程**：
* 点击仓库上方的 `Actions` 选项卡。
* 点击 `I understand my workflows, go ahead and enable them`。
* 在左侧选择 `Chengdu Air Quality Daily Report`，手动点击 `Run workflow` 进行第一次测试。



### 3. 本地运行

如果你想在本地运行测试，请先安装依赖：

```bash
pip install requests chinesecalendar urllib3

```

然后设置环境变量并执行：

```bash
export SEND_KEY="你的Key"
python main.py

```

## ⚙️ 配置说明

### 切换城市

本项目默认监测**成都市**。如果你在四川省内其他城市（如绵阳、宜宾等），只需修改 `main.py` 中的筛选逻辑：

```python
# 修改 get_yesterday_aqi 中的：
if city['name'] == "成都市": # 改为你的城市名

# 修改 get_forecast 中的：
if city['cityName'] == "成都市": # 改为你的城市名

```

### 定时时间

自动化执行时间在 `.github/workflows/daily_report.yml` 中配置：

```yaml
on:
  schedule:
    - cron: '30 0 * * *' # 对应北京时间 08:30

```

## 📊 消息示例

推送至微信的消息包含如下结构：

> **熊猫 成都空气质量及限行日报 (2026-01-06)**
> **📊 成都实况数据**
> * AQI指数: `165` (🔴 中度)
> * 首要污染物: `PM2.5`
> 
> 
> **🚗 今日限行规定**
> 🟠 **橙色预警限行**
> * 时间: **06:00 - 22:00**
> * 范围: 四环路(绕城)以内区域道路
> * 规则: 小客车(尾号 2 和 7)及货车均限行
> 
> 
> **📈 未来7天趋势预测**
> (表格展示日期、星期、AQI范围、等级等...)

## 🛠️ 技术栈

* **Python 3.9+**
* **GitHub Actions**: 自动化 CI/CD。
* **Server酱**: 微信消息推送。
* **四川省生态环境厅 API**: 权威数据来源。

## ⚖️ 免责声明

* 本项目仅供技术研究和个人生活参考。
* 限行信息根据公开 API 计算，具体限行规则请以官方发布的最新通告为准。
* 数据来源于第三方接口，不保证 100% 的实时性或准确性。

---

**如果你觉得这个项目有用，欢迎给一个 ⭐️ Star！**

---
