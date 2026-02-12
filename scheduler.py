"""
定时任务调度器 - 每天上午 10:00 自动执行
"""

import schedule
import time
import logging
from datetime import datetime
from typing import Callable, Optional

from config import app_config

logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器 - 支持多周期任务"""

    def __init__(self):
        self.tasks: dict = {}  # 存储多个任务 {period: task}
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[bool] = None
        self.error_message: Optional[str] = None

        # 设置时区
        schedule.timezone = app_config.TIMEZONE

    def set_task(self, task: Callable, period: str = "daily"):
        """
        设置要执行的任务

        Args:
            task: 无参数的函数
            period: 周期类型 (daily, weekly, monthly)
        """
        self.tasks[period] = task
        logger.info(f"任务已设置 [{period}]: {task.__name__}")

    def _run_job(self, period: str = "daily"):
        """执行任务
        
        Args:
            period: 周期类型 (daily, weekly, monthly)
        """
        task = self.tasks.get(period)
        if not task:
            logger.error(f"没有设置 [{period}] 任务")
            return

        logger.info("=" * 50)
        logger.info(f"开始执行 [{period}] 定时任务: {datetime.now()}")
        logger.info("=" * 50)

        self.is_running = True
        self.error_message = None

        try:
            task()
            self.last_result = True
            logger.info(f"✅ [{period}] 任务执行成功")
        except Exception as e:
            self.last_result = False
            self.error_message = str(e)
            logger.error(f"❌ [{period}] 任务执行失败: {e}")
        finally:
            self.is_running = False
            self.last_run = datetime.now()

    def start(self, hour: int = None, minute: int = None):
        """
        启动定时任务（支持多周期）

        Args:
            hour: 执行小时（默认从配置读取）
            minute: 执行分钟（默认从配置读取）
        """
        if not self.tasks:
            logger.error("请先设置任务（调用 set_task）")
            return

        hour = hour if hour is not None else app_config.SCHEDULE_HOUR
        minute = minute if minute is not None else app_config.SCHEDULE_MINUTE

        # 清除所有已存在的任务
        schedule.clear()

        # 为每个周期设置调度
        for period, task in self.tasks.items():
            if period == "daily":
                # 每日执行
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._run_job, period="daily")
                logger.info(f"📅 每日任务已设置: 每天 {hour:02d}:{minute:02d}")
            elif period == "weekly":
                # 每周一执行
                schedule.every().monday.at(f"{hour:02d}:{minute:02d}").do(self._run_job, period="weekly")
                logger.info(f"📅 每周任务已设置: 每周一 {hour:02d}:{minute:02d}")
            elif period == "monthly":
                # 每月1号执行
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                    self._run_monthly_job, hour=hour, minute=minute
                )
                logger.info(f"📅 每月任务已设置: 每月1号 {hour:02d}:{minute:02d}")

        logger.info(f"   时区: {app_config.TIMEZONE}")

    def _run_monthly_job(self, hour: int, minute: int):
        """每月任务检查器（在每月1号执行）"""
        today = datetime.now()
        if today.day == 1:
            self._run_job(period="monthly")

    def run_now(self, period: str = "daily"):
        """立即执行一次任务
        
        Args:
            period: 周期类型 (daily, weekly, monthly)
        """
        logger.info(f"🚀 收到手动执行命令 [{period}]")
        self._run_job(period=period)

    def stop(self):
        """停止定时任务"""
        schedule.clear()
        self.is_running = False
        logger.info("🛑 定时任务已停止")

    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
            "error": self.error_message,
            "next_run": str(schedule.next_run()) if schedule.jobs else None,
            "timezone": app_config.TIMEZONE,
            "configured_periods": list(self.tasks.keys())
        }

    def run_scheduler(self):
        """运行调度器（阻塞模式）"""
        logger.info("🔄 调度器开始运行（按 Ctrl+C 退出）")

        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # 每 30 秒检查一次
        except KeyboardInterrupt:
            logger.info("\n👋 收到中断信号，正在停止...")
            self.stop()
        except Exception as e:
            logger.error(f"调度器异常: {e}")
            self.stop()
            raise


# 全局调度器实例
scheduler = Scheduler()


def start_daily_schedule(task: Callable):
    """
    便捷函数：启动每日定时任务（向后兼容）

    Args:
        task: 要执行的任务函数
    """
    scheduler.set_task(task, period="daily")
    scheduler.start()


if __name__ == "__main__":
    # 测试调度器（多周期）
    logging.basicConfig(level=logging.INFO)

    def test_daily():
        print("🎉 每日任务执行！")
        print(f"时间: {datetime.now()}")

    def test_weekly():
        print("🎉 每周任务执行！")
        print(f"时间: {datetime.now()}")

    scheduler.set_task(test_daily, period="daily")
    scheduler.set_task(test_weekly, period="weekly")
    scheduler.start(hour=10, minute=0)

    # 显示状态
    print("\n调度器状态:")
    print(scheduler.get_status())

    # 运行 5 秒后退出（演示用）
    print("\n运行 5 秒后退出...")
    time.sleep(5)

    # 立即执行一次
    print("\n立即执行每日任务...")
    scheduler.run_now(period="daily")

    scheduler.stop()
    print("测试完成")
