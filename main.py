# coding=utf-8
"""
热点新闻爬虫主程序
整合调度器和Web服务
"""

import logging
import signal
import sys
import yaml
from threading import Thread
from pathlib import Path

from src.scheduler import NewsScheduler
from src.web.app import create_app


def setup_logging(config):
    """配置日志系统"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'logs/crawler.log')
    max_bytes = log_config.get('max_bytes', 10485760)  # 10MB
    backup_count = log_config.get('backup_count', 5)

    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # 配置日志格式
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成: {log_file}")
    return logger


def run_scheduler(scheduler):
    """运行调度器（在单独线程中）"""
    try:
        scheduler.start()
    except Exception as e:
        logging.error(f"调度器运行失败: {e}")


def main():
    """主函数"""
    # 加载配置
    config_path = "config/config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 配置日志
    logger = setup_logging(config)
    logger.info("=" * 60)
    logger.info("热点新闻爬虫启动中...")
    logger.info("=" * 60)

    # 创建调度器
    scheduler = NewsScheduler(config_path=config_path)
    scheduler.setup_jobs()

    # 创建Flask应用
    web_config = config.get('web', {})
    app = create_app(config_path=config_path)

    # 启动参数
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if mode == 'crawl':
        # 仅运行一次爬取任务
        logger.info("模式: 单次爬取")
        scheduler.run_once()
        logger.info("爬取完成")

    elif mode == 'scheduler':
        # 仅运行调度器
        logger.info("模式: 仅调度器")
        scheduler.start()

    elif mode == 'web':
        # 仅运行Web服务
        logger.info("模式: 仅Web服务")
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 5000)
        debug = web_config.get('debug', False)

        logger.info(f"Web服务启动: http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)

    else:
        # 同时运行调度器和Web服务
        logger.info("模式: 调度器 + Web服务")

        # 启动时立即执行一次爬取
        logger.info("启动时执行初始爬取...")
        import threading
        initial_crawl_thread = threading.Thread(target=scheduler.run_once, daemon=True)
        initial_crawl_thread.start()

        # 在单独线程中运行调度器
        scheduler_thread = Thread(target=run_scheduler, args=(scheduler,), daemon=True)
        scheduler_thread.start()

        # 运行Web服务
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 5000)
        debug = web_config.get('debug', False)

        logger.info(f"Web服务启动: http://{host}:{port}")
        logger.info("按 Ctrl+C 停止服务")

        try:
            app.run(host=host, port=port, debug=debug, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
            scheduler.scheduler.shutdown()
            logger.info("服务已停止")


if __name__ == '__main__':
    main()
