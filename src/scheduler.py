# coding=utf-8
"""
调度模块
负责定时任务的调度和管理
"""

import signal
import logging
import yaml
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .crawler import NewsCrawler
from .database import DatabaseManager


class NewsScheduler:
    """新闻调度器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化调度器

        Args:
            config_path: 配置文件路径
        """
        self.logger = logging.getLogger(__name__)

        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 初始化组件
        db_config = self.config.get('database', {})
        self.db = DatabaseManager(
            db_path=db_config.get('path', 'data/hotnews.db'),
            retention_days=db_config.get('retention_days', 7)
        )

        crawler_config = self.config.get('crawler', {})
        self.crawler = NewsCrawler(
            api_url=crawler_config.get('api_url', 'https://newsnow.busiyi.world/api/s'),
            request_interval=crawler_config.get('request_interval', 1),
            max_retries=crawler_config.get('max_retries', 2),
            retry_wait_min=crawler_config.get('retry_wait_min', 3),
            retry_wait_max=crawler_config.get('retry_wait_max', 5),
            timeout=crawler_config.get('timeout', 10),
        )

        # 加载平台配置
        platforms_config = Path("config/platforms.yaml")
        if platforms_config.exists():
            with open(platforms_config, 'r', encoding='utf-8') as f:
                platforms_data = yaml.safe_load(f)
                self.platforms = platforms_data.get('platforms', [])
        else:
            self.logger.warning("平台配置文件不存在，使用默认配置")
            self.platforms = []

        # 创建调度器
        self.scheduler = BlockingScheduler()

        # 添加事件监听器
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _job_executed_listener(self, event):
        """任务执行事件监听器"""
        if event.exception:
            self.logger.error(f"任务执行失败: {event.exception}")
        else:
            self.logger.info(f"任务执行成功: {event.job_id}")

    def _signal_handler(self, signum, frame):
        """信号处理器（优雅退出）"""
        self.logger.info(f"收到信号 {signum}，正在关闭调度器...")
        self.scheduler.shutdown()
        self.logger.info("调度器已关闭")

    def crawl_job(self):
        """爬取任务"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行爬取任务")

        try:
            # 爬取数据
            news_list = self.crawler.crawl_all(self.platforms)

            if news_list:
                # 存入数据库
                inserted_count = self.db.insert_news(news_list)
                self.logger.info(f"本次爬取: 新增 {inserted_count} 条新闻")
            else:
                self.logger.warning("未获取到任何新闻")

        except Exception as e:
            self.logger.error(f"爬取任务执行失败: {e}", exc_info=True)

        self.logger.info("爬取任务完成")
        self.logger.info("=" * 50)

    def cleanup_job(self):
        """清理任务（每天凌晨1点执行）"""
        self.logger.info("=" * 50)
        self.logger.info("开始执行清理任务")

        try:
            deleted_count = self.db.cleanup_old_data()
            self.logger.info(f"清理任务完成: 删除 {deleted_count} 条过期数据")
        except Exception as e:
            self.logger.error(f"清理任务执行失败: {e}", exc_info=True)

        self.logger.info("=" * 50)

    def setup_jobs(self):
        """配置定时任务"""
        scheduler_config = self.config.get('scheduler', {})

        # 爬取任务（每5分钟）
        crawl_interval = scheduler_config.get('crawl_interval', 300)  # 默认5分钟
        self.scheduler.add_job(
            self.crawl_job,
            IntervalTrigger(seconds=crawl_interval),
            id='crawl_job',
            name='爬取新闻',
            max_instances=1,
        )
        self.logger.info(f"已配置爬取任务: 每 {crawl_interval} 秒执行一次")

        # 清理任务（每天凌晨1点）
        cleanup_time = scheduler_config.get('cleanup_time', '01:00')
        hour, minute = map(int, cleanup_time.split(':'))
        self.scheduler.add_job(
            self.cleanup_job,
            CronTrigger(hour=hour, minute=minute),
            id='cleanup_job',
            name='清理过期数据',
            max_instances=1,
        )
        self.logger.info(f"已配置清理任务: 每天 {cleanup_time} 执行")

    def start(self):
        """启动调度器"""
        self.logger.info("调度器启动中...")
        self.logger.info(f"当前时区: {self.scheduler.timezone}")

        # 显示所有任务
        self.logger.info("已配置的任务:")
        for job in self.scheduler.get_jobs():
            self.logger.info(f"  - {job.name} ({job.id})")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("调度器已停止")

    def run_once(self):
        """立即执行一次爬取任务（用于测试）"""
        self.crawl_job()
