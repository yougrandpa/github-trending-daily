"""
邮件发送模块 - 支持 HTML 格式邮件
使用 SMTP 协议，支持 QQ 邮箱等主流邮件服务
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate
from typing import List, Dict
import os

from config import email_config

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""

    def __init__(self):
        self.smtp_server = email_config.SMTP_SERVER
        self.smtp_port = email_config.SMTP_PORT
        self.sender_email = email_config.SENDER_EMAIL
        self.sender_password = email_config.SENDER_PASSWORD
        self.sender_name = email_config.SENDER_NAME
        self.recipients = [email.strip() for email in email_config.RECIPIENT_EMAILS if email.strip()]
        self.subject = email_config.EMAIL_SUBJECT

    def _create_html_content(self, repos_analyzed: List[Dict], date: str = "", period: str = "daily") -> str:
        """
        生成 HTML 格式的邮件内容

        Args:
            repos_analyzed: 分析后的仓库列表
            date: 报告日期
            period: 周期类型 (daily, weekly, monthly)

        Returns:
            HTML 内容字符串
        """
        if not date:
            from datetime import datetime
            if period == "weekly":
                date = datetime.now().strftime("%Y年第%W周")
            elif period == "monthly":
                date = datetime.now().strftime("%Y年%m月")
            else:
                date = datetime.now().strftime("%Y年%m月%d日")
        
        # 周期显示文本
        period_text = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(period, "每日")

        # 构建仓库列表 HTML
        repos_html = ""
        for i, repo in enumerate(repos_analyzed, 1):
            analysis = repo.get("analysis", "")

            # 处理分析内容的格式
            if isinstance(analysis, str):
                # 将换行符转换为 <br>
                analysis_html = analysis.replace("\n", "<br>")
                # 处理 Markdown 格式
                analysis_html = self._format_markdown(analysis_html)
            else:
                # 如果是结构化数据，转换为 HTML
                analysis_html = self._format_structured_analysis(analysis)

            repos_html += f"""
            <div class="repo-card">
                <div class="repo-header">
                    <span class="repo-number">{i}</span>
                    <h3 class="repo-name">
                        <a href="{repo.get('url', '#')}" target="_blank">{repo.get('name', 'Unknown')}</a>
                    </h3>
                    <div class="repo-stats">
                        <span class="stars">⭐ {repo.get('stars', 0)}</span>
                        <span class="forks">🍴 {repo.get('forks', 0)}</span>
                    </div>
                </div>
                <div class="repo-description">{repo.get('description', '暂无描述')}</div>
                <div class="repo-analysis">
                    {analysis_html}
                </div>
            </div>
            """

        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日 GitHub 流行仓库报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header .date {{
            margin-top: 10px;
            font-size: 14px;
            opacity: 0.9;
        }}
        .content {{
            padding: 20px;
        }}
        .repo-card {{
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin-bottom: 20px;
            padding: 20px;
            background-color: #fff;
        }}
        .repo-card:hover {{
            border-color: #0366d6;
        }}
        .repo-header {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        .repo-number {{
            background-color: #0366d6;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: bold;
            margin-right: 12px;
            flex-shrink: 0;
        }}
        .repo-name {{
            margin: 0;
            font-size: 18px;
            flex-grow: 1;
        }}
        .repo-name a {{
            color: #0366d6;
            text-decoration: none;
        }}
        .repo-name a:hover {{
            text-decoration: underline;
        }}
        .repo-stats {{
            font-size: 14px;
            color: #586069;
        }}
        .repo-stats span {{
            margin-left: 12px;
        }}
        .repo-description {{
            color: #586069;
            font-size: 14px;
            margin-bottom: 12px;
            padding-left: 40px;
        }}
        .repo-analysis {{
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 15px;
            font-size: 14px;
            line-height: 1.8;
            padding-left: 40px;
        }}
        .repo-analysis h4 {{
            margin: 0 0 10px 0;
            color: #24292e;
            font-size: 14px;
        }}
        .repo-analysis ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .repo-analysis li {{
            margin-bottom: 6px;
        }}
        .footer {{
            background-color: #f6f8fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #586069;
            border-top: 1px solid #e1e4e8;
        }}
        .stats-summary {{
            display: flex;
            justify-content: center;
            gap: 30px;
            padding: 15px;
            background-color: #f6f8fa;
            border-bottom: 1px solid #e1e4e8;
        }}
        .stats-summary div {{
            text-align: center;
        }}
        .stats-summary .value {{
            font-size: 24px;
            font-weight: bold;
            color: #0366d6;
        }}
        .stats-summary .label {{
            font-size: 12px;
            color: #586069;
        }}
        @media (max-width: 600px) {{
            .repo-header {{
                flex-wrap: wrap;
            }}
            .repo-stats {{
                width: 100%;
                margin-top: 8px;
                padding-left: 40px;
            }}
            .repo-description, .repo-analysis {{
                padding-left: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {period_text}{self.subject.replace("每日", "").replace("每周", "").replace("每月", "")}</h1>
            <div class="date">{date} · GitHub {period_text}精选</div>
        </div>
        <div class="stats-summary">
            <div>
                <div class="value">{len(repos_analyzed)}</div>
                <div class="label">精选仓库</div>
            </div>
            <div>
                <div class="value">{sum(r.get('stars', 0) for r in repos_analyzed):,}</div>
                <div class="label">总 Stars</div>
            </div>
            <div>
                <div class="value">{sum(r.get('forks', 0) for r in repos_analyzed):,}</div>
                <div class="label">总 Forks</div>
            </div>
        </div>
        <div class="content">
            {repos_html}
        </div>
        <div class="footer">
            <p>🤖 此报告由 GitHub Trending Bot 自动生成</p>
            <p>📧 {period_text}定时发送</p>
        </div>
    </div>
</body>
</html>
        """
        return html_template

    def _create_text_content(self, repos_analyzed: List[Dict], date: str = "", period: str = "daily") -> str:
        """
        生成纯文本格式的邮件内容

        Args:
            repos_analyzed: 分析后的仓库列表
            date: 报告日期
            period: 周期类型 (daily, weekly, monthly)

        Returns:
            纯文本内容字符串
        """
        if not date:
            from datetime import datetime
            if period == "weekly":
                date = datetime.now().strftime("%Y年第%W周")
            elif period == "monthly":
                date = datetime.now().strftime("%Y年%m月")
            else:
                date = datetime.now().strftime("%Y年%m月%d日")
        
        # 周期显示文本
        period_text = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(period, "每日")

        lines = []
        lines.append("=" * 60)
        subject = period_text + self.subject.replace("每日", "").replace("每周", "").replace("每月", "")
        lines.append(f"📊 {subject}")
        lines.append(f"📅 {date}")
        lines.append("=" * 60)
        lines.append("")

        total_stars = 0
        total_forks = 0

        for i, repo in enumerate(repos_analyzed, 1):
            total_stars += repo.get('stars', 0)
            total_forks += repo.get('forks', 0)

            lines.append(f"【{i}】{repo.get('name', 'Unknown')}")
            lines.append(f"🔗 {repo.get('url', '#')}")
            lines.append(f"⭐ {repo.get('stars', 0)}  |  🍴 {repo.get('forks', 0)}")
            lines.append(f"📝 {repo.get('description', '暂无描述')}")
            lines.append("-" * 60)

            analysis = repo.get('analysis', '')
            if isinstance(analysis, str):
                lines.append(analysis)
            else:
                lines.append(str(analysis))

            lines.append("")
            lines.append("-" * 60)
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"📈 统计: 共 {len(repos_analyzed)} 个仓库，⭐ {total_stars:,}，🍴 {total_forks:,}")
        lines.append("🤖 此报告由 GitHub Trending Bot 自动生成")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_markdown(self, text: str) -> str:
        """简单的 Markdown 格式处理"""
        import re

        # 加粗
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # 斜体
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        # 标题 (假设使用 #### 或 ## 开头)
        text = re.sub(r'^(#+)\s*(.*)$', r'<strong>\2</strong>', text, flags=re.MULTILINE)

        # 如果文本中有列表格式，转换为 HTML 列表
        if '• ' in text or '- ' in text:
            lines = text.split('<br>')
            in_list = False
            html_lines = []

            for line in lines:
                if line.strip().startswith(('• ', '- ', '* ')):
                    if not in_list:
                        html_lines.append('<ul>')
                        in_list = True
                    content = line.strip()[2:].strip()
                    html_lines.append(f'<li>{content}</li>')
                else:
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    html_lines.append(line)

            if in_list:
                html_lines.append('</ul>')

            text = '<br>'.join(html_lines)

        return text

    def _format_structured_analysis(self, analysis: Dict) -> str:
        """格式化结构化的分析数据"""
        html_parts = []

        for key, value in analysis.items():
            if isinstance(value, list):
                items = '<br>'.join(f"• {item}" for item in value)
                html_parts.append(f"<strong>{key}:</strong><br>{items}")
            elif isinstance(value, str):
                html_parts.append(f"<strong>{key}:</strong> {value}")

        return '<br>'.join(html_parts)

    def send_email(self, repos_analyzed: List[Dict], date: str = "", period: str = "daily") -> bool:
        """
        发送邮件

        Args:
            repos_analyzed: 分析后的仓库列表
            date: 报告日期（可选）
            period: 周期类型 (daily, weekly, monthly)

        Returns:
            是否发送成功
        """
        if not self.sender_email or not self.sender_password:
            logger.error("邮件配置不完整（发件人邮箱或密码未设置）")
            return False

        if not self.recipients:
            logger.error("没有设置收件人邮箱")
            return False

        # 生成邮件内容
        html_content = self._create_html_content(repos_analyzed, date, period)
        text_content = self._create_text_content(repos_analyzed, date, period)

        # 构建邮件
        period_text = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(period, "每日")
        subject = period_text + self.subject.replace("每日", "").replace("每周", "").replace("每月", "")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{subject} - {date}" if date else subject
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = ", ".join(self.recipients)
        msg['Date'] = formatdate()
        msg['X-Mailer'] = 'GitHub-Trending-Bot/1.0'

        # 添加纯文本版本
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)

        # 添加 HTML 版本
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        try:
            logger.info(f"正在发送邮件到 {len(self.recipients)} 个收件人...")

            # 连接 SMTP 服务器
            if self.smtp_port == 465:
                # SSL 连接
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
            else:
                # TLS 连接
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                server.starttls()

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, self.recipients, msg.as_string())
            server.quit()

            logger.info(f"✅ 邮件发送成功！收件人: {', '.join(self.recipients)}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ 邮件发送失败：认证错误，请检查邮箱和授权码")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ 邮件发送失败：{e}")
            return False
        except Exception as e:
            logger.error(f"❌ 邮件发送失败（未知错误）：{e}")
            return False


# 便捷函数
def send_daily_report(repos_analyzed: List[Dict], date: str = "") -> bool:
    """发送每日报告"""
    sender = EmailSender()
    return sender.send_email(repos_analyzed, date, period="daily")


def send_weekly_report(repos_analyzed: List[Dict], date: str = "") -> bool:
    """发送每周报告"""
    sender = EmailSender()
    return sender.send_email(repos_analyzed, date, period="weekly")


def send_monthly_report(repos_analyzed: List[Dict], date: str = "") -> bool:
    """发送每月报告"""
    sender = EmailSender()
    return sender.send_email(repos_analyzed, date, period="monthly")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 测试数据
    test_repos = [
        {
            "name": "zustand-js/zustand",
            "url": "https://github.com/zustand-js/zustand",
            "stars": 35000,
            "forks": 1500,
            "description": "A small, fast and scalable bearbones state-management solution using simplified flux principles.",
            "language": "TypeScript",
            "analysis": "这是一个轻量级的状态管理库，特别适合 React 应用。"
        },
        {
            "name": "shadcn-ui/ui",
            "url": "https://github.com/shadcn-ui/ui",
            "stars": 50000,
            "forks": 3000,
            "description": "Beautifully designed components built with Radix UI and Tailwind CSS.",
            "language": "TypeScript",
            "analysis": "高质量的 UI 组件库，专注于可访问性和自定义性。"
        }
    ]

    sender = EmailSender()

    # 测试生成 HTML 内容
    html = sender._create_html_content(test_repos)
    print("HTML 邮件内容生成成功！")
    print(f"大小: {len(html)} 字符")

    # 注意：实际发送需要配置正确的邮箱信息
    print("\n提示：需要配置正确的邮箱信息后才能发送邮件")
