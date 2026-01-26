"""
主程序 - 每日 GitHub 流行仓库 AI 解读邮件服务
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import app_config
from github_client import GitHubClient, get_daily_trending
from ai_analyzer import AIAnalyzer, analyze_repositories
from email_sender import EmailSender, send_daily_report
from scheduler import scheduler

# 配置日志
logging.basicConfig(
    level=getattr(logging, app_config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('github-trending.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def save_report(repos_analyzed: List[Dict], date: str = ""):
    """
    保存报告到本地文件

    Args:
        repos_analyzed: 分析后的仓库列表
        date: 报告日期
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 确保目录存在
    os.makedirs(app_config.REPORTS_DIR, exist_ok=True)

    # 保存 JSON 格式
    json_path = os.path.join(app_config.REPORTS_DIR, f"report_{date}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "repos": repos_analyzed
        }, f, ensure_ascii=False, indent=2)

    # 保存 HTML 格式
    html_path = os.path.join(app_config.REPORTS_DIR, f"report_{date}.html")
    from email_sender import EmailSender
    sender = EmailSender()
    html_content = sender._create_html_content(repos_analyzed, date)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"📁 报告已保存: {json_path}")
    logger.info(f"📁 HTML 报告已保存: {html_path}")


def generate_daily_report() -> List[Dict]:
    """
    生成每日报告的完整流程

    Returns:
        分析后的仓库列表
    """
    logger.info("=" * 60)
    logger.info("🚀 开始生成每日 GitHub Trending 报告")
    logger.info("=" * 60)

    date_str = datetime.now().strftime("%Y年%m月%d日")
    logger.info(f"📅 报告日期: {date_str}")

    # 步骤 1: 获取 GitHub Trending 仓库
    logger.info("\n📥 步骤 1/3: 正在获取 GitHub Trending 仓库...")
    try:
        repos = get_daily_trending()
        logger.info(f"   ✅ 获取到 {len(repos)} 个仓库")
    except Exception as e:
        logger.error(f"   ❌ 获取仓库失败: {e}")
        raise

    if not repos:
        logger.warning("未获取到任何仓库，任务终止")
        return []

    # 步骤 2: AI 分析
    logger.info("\n🤖 步骤 2/3: 正在调用 AI 分析仓库...")
    try:
        analyzer = AIAnalyzer()
        repos_analyzed = analyzer.analyze_repos_batch(repos, delay=1.0)
        success_count = sum(1 for r in repos_analyzed if r.get("success"))
        logger.info(f"   ✅ 完成 {success_count}/{len(repos_analyzed)} 个仓库分析")
    except Exception as e:
        logger.error(f"   ❌ AI 分析失败: {e}")
        raise

    # 步骤 3: 发送邮件和保存
    logger.info("\n📧 步骤 3/3: 正在发送邮件...")

    # 保存到本地
    if app_config.SAVE_HISTORY:
        try:
            save_report(repos_analyzed, date_str)
        except Exception as e:
            logger.warning(f"   ⚠️ 保存报告失败: {e}")

    # 发送邮件
    try:
        success = send_daily_report(repos_analyzed, date_str)
        if success:
            logger.info("   ✅ 邮件发送成功")
        else:
            logger.warning("   ⚠️ 邮件发送失败")
    except Exception as e:
        logger.error(f"   ❌ 发送邮件时出错: {e}")
        raise

    logger.info("\n" + "=" * 60)
    logger.info("✨ 每日报告生成完成！")
    logger.info("=" * 60)

    return repos_analyzed


def run_manually():
    """手动执行一次报告生成（用于测试）"""
    logger.info("🔧 手动执行模式")

    try:
        repos_analyzed = generate_daily_report()

        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 报告摘要")
        print("=" * 60)
        print(f"仓库数量: {len(repos_analyzed)}")

        total_stars = sum(r.get('stars', 0) for r in repos_analyzed)
        total_forks = sum(r.get('forks', 0) for r in repos_analyzed)
        print(f"总 Stars: {total_stars:,}")
        print(f"总 Forks: {total_forks:,}")
        print("=" * 60)

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断执行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


def run_scheduler_mode():
    """调度器模式运行"""
    logger.info("📅 调度器模式")

    # 设置任务
    scheduler.set_task(generate_daily_report)

    # 启动调度器
    scheduler.start()

    # 运行调度器（阻塞）
    scheduler.run_scheduler()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="每日 GitHub 流行仓库 AI 解读邮件服务")
    parser.add_argument('--now', action='store_true', help='立即执行一次（用于测试）')
    parser.add_argument('--hour', type=int, default=None, help='指定执行小时（0-23）')
    parser.add_argument('--minute', type=int, default=None, help='指定执行分钟（0-59）')

    args = parser.parse_args()

    # 检查关键配置
    from config import ai_config, email_config

    if not ai_config.BASE_URL or not ai_config.API_KEY:
        logger.error("❌ 错误: AI API 配置不完整")
        logger.error("   请在 .env 文件中设置 AI_BASE_URL 和 AI_API_KEY")
        sys.exit(1)

    if not email_config.SENDER_EMAIL or not email_config.RECIPIENT_EMAILS:
        logger.error("❌ 错误: 邮件配置不完整")
        logger.error("   请在 .env 文件中设置 EMAIL_SENDER 和 EMAIL_RECIPIENTS")
        sys.exit(1)

    if args.now:
        # 立即执行
        run_manually()
    else:
        # 调度器模式
        if args.hour is not None:
            scheduler.start(hour=args.hour, minute=args.minute or 0)
            scheduler.run_scheduler()
        else:
            run_scheduler_mode()


if __name__ == "__main__":
    main()
