# AGENTS.md - AI Coding Agent Guide

> 本文档面向 AI 编程助手，帮助快速理解和开发本项目。  
> **版本**: 1.0 | **最后更新**: 2026-02-12

## 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [模块职责](#模块职责)
- [核心工作流程](#核心工作流程)
- [启动方式](#启动方式)
- [环境配置](#环境配置)
- [代码规范](#代码规范)
- [测试策略](#测试策略)
- [部署方式](#部署方式)
- [安全注意事项](#安全注意事项)
- [常见问题调试](#常见问题调试)
- [扩展开发](#扩展开发)
- [文件编码](#文件编码)
- [相关资源](#相关资源)

## 项目概述

**GitHub Trending Daily** 是一个自动化服务，每天采集 GitHub 当日热门仓库，使用 AI 生成技术解读报告，并通过邮件发送。项目采用 Python 编写，使用 Web 爬虫获取 Trending 数据，调用 LLM API 进行分析，最终生成 HTML/JSON 格式的报告。

## 技术栈

- **语言**: Python 3.8+
- **核心依赖**:
  - `requests` - HTTP 请求（GitHub API 和 Web 页面爬取）
  - `beautifulsoup4` - HTML 解析（爬取 GitHub Trending 页面）
  - `schedule` - 定时任务调度
  - `python-dotenv` - 环境变量管理
  - `colorlog` - 彩色日志输出（可选）

## 项目结构

```
github-trending-daily/
├── main.py              # 主程序入口，协调各模块工作流
├── config.py            # 配置管理（环境变量 → 配置类）
├── github_client.py     # GitHub 数据获取模块
├── ai_analyzer.py       # AI 分析模块（调用 LLM API）
├── email_sender.py      # 邮件发送模块（SMTP/HTML 生成）
├── scheduler.py         # 定时任务调度器
├── run.sh               # 启动脚本（自动管理虚拟环境）
├── requirements.txt     # Python 依赖列表
├── .env.example         # 环境变量配置示例
├── reports/             # 历史报告存储目录（JSON + HTML）
└── github-trending.log  # 运行日志
```

## 模块职责

### 1. github_client.py
- **职责**: 获取 GitHub Trending 仓库数据
- **输入**: 语言筛选、周期类型 (`daily`/`weekly`/`monthly`)
- **输出**: `List[Dict]` 仓库信息列表
- **实现方式**: 使用 `requests` + `BeautifulSoup` 爬取 `https://github.com/trending` 页面，支持 `?since=` 参数指定周期
- **关键字段**: 仓库名称、描述、语言、stars、forks、今日/本周/本月新增 stars
- **周期支持**: `daily` (今日), `weekly` (本周), `monthly` (本月)
- **注意**: 不依赖 GitHub API，而是直接解析 HTML（CSS 选择器在 2025-2026 期间稳定）

### 2. ai_analyzer.py
- **职责**: 调用 AI API 为每个仓库生成技术解读
- **输入**: `List[Dict]` 仓库信息列表
- **输出**: `List[Dict]` 带 AI 分析结果的仓库列表
- **支持的 API**: OpenAI、Claude、NVIDIA API 或其他兼容 OpenAI 格式的服务
- **分析维度**: 项目亮点、适用场景、技术栈、同类对比、上手难度、活跃度、目标用户
- **重试机制**: 指数退避重试（最多 3 次），支持流式响应处理

### 3. email_sender.py
- **职责**: 生成并发送 HTML 格式邮件
- **输入**: `List[Dict]` 带分析的仓库数据，收件人列表
- **输出**: 邮件发送状态（布尔值）
- **邮件内容**: 包含统计概览、仓库列表、AI 分析结果
- **响应式设计**: 邮件模板支持移动端和桌面端
- **SMTP 支持**: SSL (465) 和 TLS (587) 两种连接方式

### 4. scheduler.py
- **职责**: 定时任务管理（支持多周期）
- **输入**: 执行时间配置（时、分）、周期类型列表
- **输出**: 无（阻塞运行调度循环）
- **调度库**: `schedule`（轻量级，每 30 秒检查一次任务）
- **周期调度**:
  - `daily`: 每天指定时间执行
  - `weekly`: 每周一指定时间执行
  - `monthly`: 每月1号指定时间执行
- **默认时间**: 每天上午 10:00 (Asia/Shanghai 时区)
- **运行模式**: 阻塞模式（主线程运行调度循环）

### 5. config.py
- **职责**: 统一管理项目配置
- **输入**: 环境变量（`.env` 文件或系统环境变量）
- **输出**: 各配置类实例
- **配置分类**: GitHubConfig、AIConfig、EmailConfig、AppConfig
- **配置来源**: 环境变量（通过 `.env` 文件加载）
- **提示词配置**: AI 的 system_prompt 和 user_prompt_template 可直接在此修改

## 核心工作流程

```
main.py
  │
  ├─→ github_client.get_trending_repos(period)  # 爬取 Trending 页面（支持 daily/weekly/monthly）
  │
  ├─→ ai_analyzer.analyze_repos_batch()         # 逐个调用 AI 分析
  │
  ├─→ save_report()                             # 保存 JSON + HTML 到 reports/
  │
  └─→ email_sender.send_email()                 # 发送邮件给收件人列表
```

## 启动方式

项目使用 `run.sh` 作为统一入口，自动处理虚拟环境和依赖：

```bash
# 查看帮助
./run.sh --help

# 立即执行一次（测试用）
./run.sh --now                   # 默认执行每日报告
./run.sh --now --period weekly   # 执行每周报告
./run.sh --now --period monthly  # 执行每月报告
./run.sh --now --period all      # 执行所有配置的周期

# 启动定时调度（默认每天 10:00）
./run.sh

# 自定义执行时间
./run.sh --hour 9 --minute 30
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--now` | 立即执行一次 | `./run.sh --now` |
| `--period <类型>` | 指定报告周期 | `./run.sh --now --period weekly` |
| `--hour <小时>` | 指定执行小时 (0-23) | `./run.sh --hour 9` |
| `--minute <分钟>` | 指定执行分钟 (0-59) | `./run.sh --minute 30` |
| `--help, -h` | 显示帮助信息 | `./run.sh --help` |

**period 可选值**: `daily` (每日), `weekly` (每周), `monthly` (每月), `all` (全部)

## 环境配置

复制 `.env.example` 为 `.env`，填写以下配置项：

### 必填项

```env
# AI API 配置
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-your-api-key
AI_MODEL=gpt-3.5-turbo

# 邮件配置（QQ 邮箱示例）
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_SENDER=your-email@qq.com
EMAIL_PASSWORD=your-authorization-code  # QQ 邮箱使用授权码，非登录密码
EMAIL_RECIPIENTS=recipient@example.com
```

### 可选项

```env
# 调度配置
SCHEDULE_HOUR=10          # 定时执行小时（默认 10）
SCHEDULE_MINUTE=0         # 定时执行分钟（默认 0）

# AI 配置
AI_TIMEOUT=60             # API 超时时间（秒，默认 60）
AI_MAX_RETRIES=3          # 最大重试次数（默认 3）
AI_TEMPERATURE=0.7        # 生成温度（默认 0.7）

# 应用配置
LOG_LEVEL=INFO            # 日志级别（默认 INFO）
MAX_REPOS=10              # 最大分析仓库数（默认 10）

# 周期配置（多周期支持）
TRENDING_PERIODS=daily           # 启用的周期，可选: daily, weekly, monthly, all（多个用逗号分隔）
DAILY_SUBJECT_PREFIX=每日        # 每日邮件主题前缀
WEEKLY_SUBJECT_PREFIX=每周       # 每周邮件主题前缀
MONTHLY_SUBJECT_PREFIX=每月      # 每月邮件主题前缀
```

## 代码规范

- **注释**: 使用中文注释，文档字符串使用 `"""三重引号"""`
- **类型提示**: 函数参数和返回值使用 Python type hints
- **日志**: 使用 `logging` 模块，格式为 `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
- **错误处理**: 关键操作使用 try-except 捕获，日志记录错误信息

## 测试策略

本项目**没有单元测试**，采用手动集成测试：

```bash
# 测试完整流程
./run.sh --now

# 测试单个模块
python3 github_client.py  # 测试数据获取
python3 ai_analyzer.py    # 测试 AI 分析
python3 email_sender.py   # 测试邮件生成（不实际发送）
```

## 部署方式

### 方式 1: 直接运行（开发/测试）
```bash
./run.sh --now
```

### 方式 2: 定时任务（生产）

**macOS - launchd:**
创建 `~/Library/LaunchAgents/com.github.trending.plist`，配置每日运行。

**Linux/macOS - cron:**
```bash
# 每天上午 10:00 执行
0 10 * * * /path/to/github-trending-daily/run.sh --now
```

**后台运行:**
```bash
nohup ./run.sh > /dev/null 2>&1 &
```

## 安全注意事项

1. **敏感信息**: API 密钥和邮箱密码通过环境变量管理，`.env` 文件已加入 `.gitignore`
2. **日志文件**: `github-trending.log` 可能包含敏感信息，注意保护
3. **报告文件**: `reports/` 目录下的 JSON/HTML 文件包含历史数据，可能涉及敏感仓库信息
4. **API 限流**:
   - GitHub 网页爬取无明确限流，但建议保持合理频率
   - AI API 调用有速率限制，已实现 1 秒延迟和指数退避重试

## 常见问题调试

| 问题 | 排查方向 |
|------|----------|
| 获取仓库失败 | 检查网络连接，GitHub Trending 页面结构是否变化，确认 period 参数正确 |
| AI 分析超时 | 检查 `AI_TIMEOUT` 配置，或 API 服务状态 |
| 邮件发送失败 | 确认 SMTP 配置，QQ 邮箱需使用授权码而非密码 |
| 依赖导入错误 | 运行 `./run.sh` 自动安装依赖，或手动 `pip install -r requirements.txt` |

## 扩展开发

### 添加新的分析维度
修改 `config.py` 中的 `AIConfig.SYSTEM_PROMPT`，添加新的分析要求。

### 修改邮件模板
编辑 `email_sender.py` 中的 `_create_html_content()` 方法，调整 HTML/CSS。

### 支持新的 AI 提供商
`ai_analyzer.py` 已支持 OpenAI 格式 API，如需特殊适配，修改 `_make_api_request()` 方法。

### 自定义调度策略
修改 `scheduler.py`，可替换为 APScheduler（已注释在 requirements.txt 中）以实现更复杂的调度需求。

### 添加新的 Trending 周期
当前支持 `daily`/`weekly`/`monthly` 三种周期：
1. 在 `config.py` 的 `TRENDING_PERIODS` 中添加新周期
2. 在 `github_client.py` 的 `get_trending_repos()` 中实现获取逻辑
3. 在 `email_sender.py` 中添加对应的邮件主题前缀
4. 在 `scheduler.py` 中添加对应的调度规则

## 文件编码

- 所有 Python 文件使用 **UTF-8** 编码
- 日志文件使用 UTF-8 编码
- 邮件内容使用 UTF-8 编码（支持中文）

## 相关资源

- [GitHub Trending](https://github.com/trending) - 官方热门仓库页面
- [项目 README](./README.md) - 面向用户的项目说明
- [schedule 文档](https://schedule.readthedocs.io/) - 定时任务库文档
