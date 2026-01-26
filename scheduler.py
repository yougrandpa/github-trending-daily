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
    """定时任务调度器"""

    def __init__(self):
        self.task: Optional[Callable] = None
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[bool] = None
        self.error_message: Optional[str] = None

        # 设置时区
        schedule.timezone = app_config.TIMEZONE

    def set_task(self, task: Callable):
        """
        设置要执行的任务

        Args:
            task: 无参数的函数
        """
        self.task = task
        logger.info(f"任务已设置: {task.__name__}")

    def _run_job(self):
        """执行任务"""
        if not self.task:
            logger.error("没有设置任务")
            return

        logger.info("=" * 50)
        logger.info(f"开始执行定时任务: {datetime.now()}")
        logger.info("=" * 50)

        self.is_running = True
        self.error_message = None

        try:
            self.task()
            self.last_result = True
            logger.info("✅ 任务执行成功")
        except Exception as e:
            self.last_result = False
            self.error_message = str(e)
            logger.error(f"❌ 任务执行失败: {e}")
        finally:
            self.is_running = False
            self.last_run = datetime.now()

    def start(self, hour: int = None, minute: int = None):
        """
        启动定时任务

        Args:
            hour: 执行小时（默认从配置读取）
            minute: 执行分钟（默认从配置读取）
        """
        if not self.task:
            logger.error("请先设置任务（调用 set_task）")
            return

        hour = hour if hour is not None else app_config.SCHEDULE_HOUR
        minute = minute if minute is not None else app_config.SCHEDULE_MINUTE

        # 清除所有已存在的任务
        schedule.clear()

        # 设置每日执行时间
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._run_job)

        logger.info(f"📅 定时任务已启动")
        logger.info(f"   执行时间: 每天 {hour:02d}:{minute:02d} ({app_config.TIMEZONE})")
        logger.info(f"   任务: {self.task.__name__}")

    def run_now(self):
        """立即执行一次任务"""
        logger.info("🚀 收到手动执行命令")
        self._run_job()

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
            "timezone": app_config.TIMEZONE
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
    便捷函数：启动每日定时任务

    Args:
        task: 要执行的任务函数
    """
    scheduler.set_task(task)
    scheduler.start()


if __name__ == "__main__":
    # 测试调度器
    logging.basicConfig(level=logging.INFO)

    def test_task():
        print("🎉 任务执行！")
        print(f"时间: {datetime.now()}")

    scheduler.set_task(test_task)
    scheduler.start(hour=10, minute=0)

    # 显示状态
    print("\n调度器状态:")
    print(scheduler.get_status())

    # 运行 5 秒后退出（演示用）
    print("\n运行 5 秒后退出...")
    time.sleep(5)

    # 立即执行一次
    print("\n立即执行一次...")
    scheduler.run_now()

    scheduler.stop()
    print("测试完成")
