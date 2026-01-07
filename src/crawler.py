# coding=utf-8
"""
爬虫模块
负责从NewsNow API抓取热点新闻数据
"""

import json
import random
import time
import logging
import requests
from typing import Dict, List, Tuple, Optional


class NewsCrawler:
    """新闻爬虫"""

    # 默认请求头
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }

    def __init__(
        self,
        api_url: str = "https://newsnow.busiyi.world/api/s",
        request_interval: int = 1,
        max_retries: int = 2,
        retry_wait_min: int = 3,
        retry_wait_max: int = 5,
        timeout: int = 10,
    ):
        """
        初始化爬虫

        Args:
            api_url: API基础URL
            request_interval: 请求间隔（秒）
            max_retries: 最大重试次数
            retry_wait_min: 最小重试等待时间（秒）
            retry_wait_max: 最大重试等待时间（秒）
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url
        self.request_interval = request_interval
        self.max_retries = max_retries
        self.retry_wait_min = retry_wait_min
        self.retry_wait_max = retry_wait_max
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def fetch_data(self, platform_id: str, platform_name: str) -> Optional[List[Dict]]:
        """
        获取单个平台的数据

        Args:
            platform_id: 平台ID
            platform_name: 平台名称

        Returns:
            新闻列表 [{title, url, mobile_url, rank}]
        """
        url = f"{self.api_url}?id={platform_id}&latest"

        retries = 0
        while retries <= self.max_retries:
            try:
                self.logger.info(f"正在抓取 {platform_name} (尝试 {retries + 1}/{self.max_retries + 1})")

                response = requests.get(
                    url,
                    headers=self.DEFAULT_HEADERS,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # 解析JSON
                data = response.json()
                status = data.get("status", "未知")

                if status not in ["success", "cache"]:
                    raise ValueError(f"响应状态异常: {status}")

                # 提取新闻列表
                items = data.get("items", [])
                news_list = []

                for index, item in enumerate(items, 1):
                    title = item.get("title")

                    # 跳过无效标题
                    if not title or isinstance(title, float) or not str(title).strip():
                        continue

                    title = str(title).strip()
                    url = item.get("url", "")
                    mobile_url = item.get("mobileUrl", "")

                    news_list.append({
                        "title": title,
                        "source": platform_name,
                        "url": url or mobile_url,  # 优先使用PC URL，为空则用移动URL
                        "rank": index,
                    })

                status_info = "最新数据" if status == "success" else "缓存数据"
                self.logger.info(f"✓ {platform_name}: 获取 {len(news_list)} 条 ({status_info})")

                return news_list

            except requests.exceptions.RequestException as e:
                retries += 1
                if retries <= self.max_retries:
                    # 随机等待后重试
                    wait_time = random.uniform(self.retry_wait_min, self.retry_wait_max)
                    self.logger.warning(f"✗ {platform_name}: 请求失败 - {e}. {wait_time:.1f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"✗ {platform_name}: 请求失败，已达最大重试次数 - {e}")
                    return None

            except json.JSONDecodeError as e:
                self.logger.error(f"✗ {platform_name}: JSON解析失败 - {e}")
                return None

            except Exception as e:
                self.logger.error(f"✗ {platform_name}: 未知错误 - {e}")
                return None

        return None

    def crawl_all(self, platforms: List[Dict]) -> List[Dict]:
        """
        批量爬取所有平台的数据

        Args:
            platforms: 平台列表 [{id, name, enabled}]

        Returns:
            所有新闻列表
        """
        all_news = []

        # 过滤启用的平台
        enabled_platforms = [p for p in platforms if p.get("enabled", True)]

        self.logger.info(f"开始爬取 {len(enabled_platforms)} 个平台的数据")

        for i, platform in enumerate(enabled_platforms):
            platform_id = platform.get("id")
            platform_name = platform.get("name")

            if not platform_id or not platform_name:
                continue

            # 抓取数据
            news_list = self.fetch_data(platform_id, platform_name)

            if news_list:
                all_news.extend(news_list)

            # 请求间隔（最后一个不等待）
            if i < len(enabled_platforms) - 1:
                time.sleep(self.request_interval)

        self.logger.info(f"爬取完成: 共获取 {len(all_news)} 条新闻")

        return all_news
