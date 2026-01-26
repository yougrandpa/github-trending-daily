# 📊 每日 GitHub 流行仓库 AI 解读邮件服务

自动采集 GitHub 当日热门仓库，使用 AI 生成详细解读，并在每天上午 10:00 通过邮件发送报告。

## ✨ 功能特性

- 🤖 **AI 智能分析** - 使用 AI 为每个仓库生成技术亮点、适用场景等深度分析
- 📧 **定时邮件发送** - 每天上午 10:00 自动发送 HTML 格式邮件报告
- 📁 **本地历史保存** - 自动保存 JSON 和 HTML 格式的历史报告
- 🔧 **高度可配置** - 支持自定义 API、调度时间、邮件模板
- 🖥️ **macOS/Linux 支持** - 原生支持 macOS 和 Linux 系统

## 🚀 快速开始

### 1. 克隆项目

```bash
cd /Users/slg/text_to_viece/tools
git clone https://github.com/your-repo/github-trending-daily.git
cd github-trending-daily
```

### 2. 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
vim .env
```

#### 必填配置项

```env
# AI API 配置（支持 OpenAI、Claude 或其他兼容 API）
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-your-api-key
AI_MODEL=gpt-3.5-turbo

# 邮件配置（QQ 邮箱示例）
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_SENDER=your-email@qq.com
EMAIL_PASSWORD=your-authorization-code
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

#### QQ 邮箱授权码获取

1. 登录 [QQ 邮箱](https://mail.qq.com)
2. 进入「设置」→「账户」
3. 开启「POP3/SMTP服务」
4. 点击「生成授权码」

### 3. 安装依赖

```bash
# 使用启动脚本（自动创建虚拟环境并安装依赖）
./run.sh --help
```

或者手动安装：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 测试运行

```bash
# 立即执行一次（用于测试配置是否正确）
./run.sh --now
```

### 5. 启动定时任务

```bash
# 启动调度器（默认每天上午 10:00 执行）
./run.sh

# 自定义执行时间
./run.sh --hour 9 --minute 30
```

## 📁 项目结构

```
github-trending-daily/
├── config.py              # 配置文件（从环境变量读取）
├── config_example.py      # 配置示例（已被 .env.example 替代）
├── github_client.py       # GitHub API 客户端
├── ai_analyzer.py         # AI 分析模块
├── email_sender.py        # 邮件发送模块
├── scheduler.py           # 定时任务调度器
├── main.py               # 主程序入口
├── run.sh               # 启动脚本
├── requirements.txt      # Python 依赖
├── .env.example         # 环境变量示例
├── reports/             # 历史报告存储目录
├── github-trending.log  # 日志文件
└── README.md            # 项目说明
```

## ⚙️ 配置说明

### 完整配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `GITHUB_TOKEN` | GitHub API Token（可选，增加请求限制） | 空 |
| `GITHUB_LANGUAGE` | 筛选编程语言（留空则获取所有） | 空 |
| `MAX_REPOSITORIES` | 每次采集的仓库数量 | 10 |
| `AI_BASE_URL` | AI API 基础地址 | 必填 |
| `AI_API_KEY` | AI API 密钥 | 必填 |
| `AI_MODEL` | 使用的模型 | gpt-3.5-turbo |
| `AI_TEMPERATURE` | AI 温度参数（0-1） | 0.7 |
| `EMAIL_SMTP_SERVER` | SMTP 服务器地址 | smtp.qq.com |
| `EMAIL_SMTP_PORT` | SMTP 端口（465 为 SSL，587 为 TLS） | 465 |
| `EMAIL_SENDER` | 发件人邮箱 | 必填 |
| `EMAIL_PASSWORD` | 发件人密码或授权码 | 必填 |
| `EMAIL_RECIPIENTS` | 收件人邮箱（逗号分隔） | 必填 |
| `SCHEDULE_HOUR` | 发送时间（小时） | 10 |
| `SCHEDULE_MINUTE` | 发送时间（分钟） | 0 |
| `TIMEZONE` | 时区 | Asia/Shanghai |

### AI 模型配置示例

#### OpenAI

```env
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-your-openai-api-key
AI_MODEL=gpt-3.5-turbo
```

#### Claude (Anthropic)

```env
AI_BASE_URL=https://api.anthropic.com/v1
AI_API_KEY=your-claude-api-key
AI_MODEL=claude-3-sonnet-20240229
```

#### 自定义代理/私有部署

```env
AI_BASE_URL=https://your-proxy.com/v1
AI_API_KEY=your-api-key
AI_MODEL=gpt-3.5-turbo
```

## 📧 邮件预览

报告邮件包含以下内容：

- **统计概览** - 今日精选仓库数量、总 Stars、总 Forks
- **仓库列表** - 每个仓库包含：
  - 仓库名称和链接
  - Stars 和 Forks 数量
  - 项目描述
  - AI 生成的技术分析
- **响应式设计** - 在手机和电脑上都能完美显示

## 🛠️ 系统集成

### 使用 launchd（macOS）

创建 `~/Library/LaunchAgents/com.github.trending.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.github.trending</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/github-trending-daily/run.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/github-trending-daily</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

启动服务：

```bash
launchctl load ~/Library/LaunchAgents/com.github.trending.plist
```

### 使用 cron（Linux/macOS）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天上午 10:00 执行）
0 10 * * * /path/to/github-trending-daily/run.sh --now
```

## 📝 使用指南

### 命令行参数

```bash
./run.sh --now              # 立即执行一次
./run.sh --hour 9 --minute 0 # 设置为每天 9:00 执行
./run.sh --help             # 显示帮助
```

### 查看日志

```bash
# 实时查看日志
tail -f github-trending.log
```

### 查看历史报告

```bash
# 查看已保存的报告
ls reports/
cat reports/report_2024-01-15.json
```

## 🐛 常见问题

### 1. 邮件发送失败

- 检查 `EMAIL_SMTP_SERVER` 和 `EMAIL_SMTP_PORT` 是否正确
- QQ 邮箱需要使用**授权码**而非登录密码
- 确保 SMTP 服务已开启

### 2. AI 分析失败

- 检查 `AI_BASE_URL` 是否可访问
- 确认 `AI_API_KEY` 正确且未过期
- 查看日志中的详细错误信息

### 3. GitHub API 限流

- 设置 `GITHUB_TOKEN` 增加请求限制
- 减少 `MAX_REPOSITORIES` 的值
- 添加请求延迟（修改代码中的 `time.sleep()`）

### 4. 时区问题

- 确保 `TIMEZONE` 配置正确
- macOS 用户：检查系统偏好设置中的时区
- Linux 用户：检查 `/etc/localtime` 或 `TZ` 环境变量

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [GitHub API](https://docs.github.com/en/rest)
- [OpenAI](https://openai.com/)
- [schedule](https://schedule.readthedocs.io/)
