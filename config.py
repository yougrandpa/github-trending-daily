"""
配置文件 - 包含所有配置项
敏感信息请从环境变量读取，不要直接写在这里
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== GitHub 配置 ====================
class GitHubConfig:
    # GitHub API 配置
    BASE_URL = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
    # 如果需要 GitHub Token（增加 API 调用限制），可以设置
    TOKEN = os.getenv("GITHUB_TOKEN", "")
    # 默认语言筛选
    DEFAULT_LANGUAGE = os.getenv("GITHUB_LANGUAGE", "")
    # 采集数量
    MAX_REPOSITORIES = int(os.getenv("MAX_REPOSITORIES", "10"))
    # 是否只获取当天的 trending
    DAILY_TRENDING = True


# ==================== AI 分析配置 ====================
class AIConfig:
    # API 基础 URL（支持自定义 API 地址，如代理或私有部署）
    BASE_URL = os.getenv("AI_BASE_URL", "").rstrip("/")
    API_KEY = os.getenv("AI_API_KEY", "")
    # 默认模型
    MODEL = os.getenv("AI_MODEL", "")
    # 请求超时时间（秒）
    TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))
    # 最大重试次数
    MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "3"))
    # temperature（0-1，越高越有创造性）
    TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

    # AI 提示词模板（可以自定义）
    SYSTEM_PROMPT = """你是一个专业的技术分析师，专门分析 GitHub 上的热门开源项目。
你的任务是生成清晰、有见地的仓库分析报告，帮助开发者了解项目的价值和适用场景。

请为每个仓库提供以下分析：
1. **项目亮点** - 这个项目最吸引人的特点
2. **适用场景** - 这个项目最适合用于什么情况
3. **技术栈/核心依赖** - 使用的主要技术
4. **与同类项目对比** - 优势和劣势
5. **上手难度** - 学习曲线评估
6. **活跃度评估** - 社区和更新频率
7. **目标用户** - 适合哪些开发者

请保持分析简洁有力，每点 1-2 句话。"""

    USER_PROMPT_TEMPLATE = """请分析以下 GitHub 仓库：

仓库名称：{name}
仓库地址：{url}
Stars：{stars}
Forks：{forks}
描述：{description}
主要语言：{language}
更新时间：{updated_at}

请按照系统提示的要求，生成详细的分析报告。"""


# ==================== 邮件配置 ====================
class EmailConfig:
    # SMTP 服务器配置
    SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "465"))
    # 发件人邮箱和授权码
    SENDER_EMAIL = os.getenv("EMAIL_SENDER", "")
    SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    # 收件人邮箱（多个用逗号分隔）
    RECIPIENT_EMAILS = os.getenv("EMAIL_RECIPIENTS", "").split(",")
    # 发件人名称
    SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "GitHub Trending Bot")
    # 邮件主题
    EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "每日 GitHub 流行仓库报告")


# ==================== 应用配置 ====================
class AppConfig:
    # 是否开启调试模式
    DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    # 时区设置
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Shanghai")
    # 定时发送时间（小时）
    SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "10"))
    # 定时发送时间（分钟）
    SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
    # 日志级别
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # 报告保存路径
    REPORTS_DIR = os.getenv("REPORTS_DIR", "./reports")
    # 是否保存历史报告
    SAVE_HISTORY = True


# 导出配置实例
github_config = GitHubConfig()
ai_config = AIConfig()
email_config = EmailConfig()
app_config = AppConfig()
