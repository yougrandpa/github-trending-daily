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

from config import app_config, github_config
from github_client import GitHubClient, get_daily_trending, get_weekly_trending, get_monthly_trending
from ai_analyzer import AIAnalyzer, analyze_repositories
from email_sender import EmailSender, send_daily_report, send_weekly_report, send_monthly_report
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


def save_report(repos_analyzed: List[Dict], date: str = "", period: str = "daily"):
    """
    保存报告到本地文件

    Args:
        repos_analyzed: 分析后的仓库列表
        date: 报告日期
        period: 周期类型 (daily, weekly, monthly)
    """
    if not date:
        if period == "weekly":
            date = datetime.now().strftime("%Y-W%W")
        elif period == "monthly":
            date = datetime.now().strftime("%Y-%m")
        else:
            date = datetime.now().strftime("%Y-%m-%d")

    # 确保目录存在
    os.makedirs(app_config.REPORTS_DIR, exist_ok=True)

    # 保存 JSON 格式
    json_path = os.path.join(app_config.REPORTS_DIR, f"report_{period}_{date}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date,
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "repos": repos_analyzed
        }, f, ensure_ascii=False, indent=2)

    # 保存 HTML 格式
    html_path = os.path.join(app_config.REPORTS_DIR, f"report_{period}_{date}.html")
    from email_sender import EmailSender
    sender = EmailSender()
    period_text = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(period, "每日")
    html_content = sender._create_html_content(repos_analyzed, date, period)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"📁 报告已保存: {json_path}")
    logger.info(f"📁 HTML 报告已保存: {html_path}")


def generate_report(period: str = "daily") -> List[Dict]:
    """
    生成报告的完整流程（支持 daily/weekly/monthly）

    Args:
        period: 周期类型 (daily, weekly, monthly)

    Returns:
        分析后的仓库列表
    """
    period_text = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(period, "每日")
    
    logger.info("=" * 60)
    logger.info(f"🚀 开始生成{period_text} GitHub Trending 报告")
    logger.info("=" * 60)

    # 根据周期设置日期格式
    if period == "weekly":
        date_str = datetime.now().strftime("%Y年第%W周")
    elif period == "monthly":
        date_str = datetime.now().strftime("%Y年%m月")
    else:
        date_str = datetime.now().strftime("%Y年%m月%d日")
    
    logger.info(f"📅 报告日期: {date_str}")

    # 步骤 1: 获取 GitHub Trending 仓库
    logger.info(f"\n📥 步骤 1/3: 正在获取 GitHub {period_text} Trending 仓库...")
    try:
        if period == "weekly":
            repos = get_weekly_trending()
        elif period == "monthly":
            repos = get_monthly_trending()
        else:
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
            save_report(repos_analyzed, date_str, period)
        except Exception as e:
            logger.warning(f"   ⚠️ 保存报告失败: {e}")

    # 发送邮件
    try:
        if period == "weekly":
            success = send_weekly_report(repos_analyzed, date_str)
        elif period == "monthly":
            success = send_monthly_report(repos_analyzed, date_str)
        else:
            success = send_daily_report(repos_analyzed, date_str)
            
        if success:
            logger.info("   ✅ 邮件发送成功")
        else:
            logger.warning("   ⚠️ 邮件发送失败")
    except Exception as e:
        logger.error(f"   ❌ 发送邮件时出错: {e}")
        raise

    logger.info("\n" + "=" * 60)
    logger.info(f"✨ {period_text}报告生成完成！")
    logger.info("=" * 60)

    return repos_analyzed


def generate_daily_report() -> List[Dict]:
    """生成每日报告（向后兼容）"""
    return generate_report(period="daily")


def run_manually(period: str = "daily"):
    """手动执行一次报告生成（用于测试）
    
    Args:
        period: 周期类型 (daily, weekly, monthly, all)
    """
    logger.info("🔧 手动执行模式")

    periods_to_run = []
    if period == "all":
        periods_to_run = [p.strip() for p in github_config.TRENDING_PERIODS if p.strip()]
    else:
        periods_to_run = [period]

    all_results = {}
    
    for p in periods_to_run:
        try:
            repos_analyzed = generate_report(period=p)
            all_results[p] = repos_analyzed

            # 打印摘要
            period_text = {"daily": "每日", "weekly": "每周", "monthly": "每月"}.get(p, p)
            print("\n" + "=" * 60)
            print(f"📊 {period_text}报告摘要")
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
            logger.error(f"生成 {p} 报告失败: {e}")
            continue
    
    return all_results


def run_scheduler_mode():
    """调度器模式运行（支持多周期）"""
    logger.info("📅 调度器模式")

    # 获取配置的周期列表
    periods = [p.strip() for p in github_config.TRENDING_PERIODS if p.strip()]
    logger.info(f"启用的周期: {periods}")

    # 为每个周期设置任务
    for period in periods:
        if period == "daily":
            scheduler.set_task(lambda: generate_report("daily"), "daily")
        elif period == "weekly":
            # 每周一执行
            scheduler.set_task(lambda: generate_report("weekly"), "weekly")
        elif period == "monthly":
            # 每月1号执行
            scheduler.set_task(lambda: generate_report("monthly"), "monthly")

    # 启动调度器
    scheduler.start()

    # 运行调度器（阻塞）
    scheduler.run_scheduler()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="GitHub 流行仓库 AI 解读邮件服务（支持每日/每周/每月）")
    parser.add_argument('--now', action='store_true', help='立即执行一次（用于测试）')
    parser.add_argument('--period', type=str, default='daily', 
                        choices=['daily', 'weekly', 'monthly', 'all'],
                        help='指定报告周期: daily(每日), weekly(每周), monthly(每月), all(全部)')
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
        # 立即执行指定周期
        run_manually(period=args.period)
    else:
        # 调度器模式
        if args.hour is not None:
            scheduler.start(hour=args.hour, minute=args.minute or 0)
            scheduler.run_scheduler()
        else:
            run_scheduler_mode()


if __name__ == "__main__":
    main()
