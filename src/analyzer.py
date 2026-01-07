# coding=utf-8
"""
统计分析模块
负责新闻数据的统计分析，包括热词统计、频率分析等
"""

import logging
import jieba
from typing import List, Dict, Tuple
from collections import Counter
from datetime import datetime, timedelta

from .database import DatabaseManager


class NewsAnalyzer:
    """新闻分析器"""

    # 停用词列表（常见无意义词汇）
    STOP_WORDS = {
        "的", "了", "是", "在", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这",
        "发布", "宣布", "表示", "称", "称将", "最新", "相关", "目前", "继续", "进行", "工作", "问题", "情况", "方面", "内容", "方式", "原因", "结果", "经过",
        "亿元", "万元", "元", "亿", "万", "年", "月", "日", "时", "分", "秒", "号", "期", "版", "篇", "条", "个", "项", "次", "件", "名", "位", "人",
    }

    def __init__(self, db: DatabaseManager):
        """
        初始化分析器

        Args:
            db: 数据库管理器实例
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

        # 初始化jieba分词
        jieba.setLogLevel(jieba.logging.INFO)

    def extract_hot_words(self, days: int = 1, top_n: int = 50) -> List[Dict]:
        """
        提取热词

        Args:
            days: 统计最近多少天的数据
            top_n: 返回前N个热词

        Returns:
            热词列表 [{word, count}]
        """
        # 获取最近N天的新闻
        news_list = self.db.get_latest_news(hours=days * 24)

        if not news_list:
            self.logger.warning("没有可分析的新闻数据")
            return []

        # 提取所有标题
        titles = [news['title'] for news in news_list]

        # 分词并统计
        all_words = []
        for title in titles:
            # 使用jieba分词
            words = jieba.lcut(title)

            # 过滤停用词和单字
            filtered_words = [
                word for word in words
                if len(word) >= 2 and word not in self.STOP_WORDS and word.isalpha()
            ]

            all_words.extend(filtered_words)

        # 统计词频
        word_counter = Counter(all_words)

        # 返回前N个热词
        hot_words = [
            {"word": word, "count": count}
            for word, count in word_counter.most_common(top_n)
        ]

        self.logger.info(f"热词分析完成: 分析了 {len(titles)} 个标题，提取 {len(hot_words)} 个热词")

        return hot_words

    def get_news_frequency(self, days: int = 7) -> List[Dict]:
        """
        获取新闻出现频率（按来源统计）

        Args:
            days: 统计最近多少天

        Returns:
            频率列表 [{source, count}]
        """
        return self.db.get_stats_by_source(days)

    def get_hourly_distribution(self, days: int = 1) -> List[Dict]:
        """
        获取每小时新闻分布

        Args:
            days: 统计最近多少天

        Returns:
            每小时分布列表 [{hour, count}]
        """
        return self.db.get_news_count_by_hour(days)

    def get_trend_data(self, days: int = 7) -> Dict:
        """
        获取趋势数据（按天统计）

        Args:
            days: 统计最近多少天

        Returns:
            趋势数据 {date: count}
        """
        trend_data = {}

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            # 查询该日期的新闻数量
            news_list, _ = self.db.get_news(
                limit=10000,
                start_date=date_str,
                end_date=date_str
            )

            trend_data[date_str] = len(news_list)

        # 按日期排序
        trend_data = dict(sorted(trend_data.items(), reverse=True))

        return trend_data

    def analyze_source_distribution(self, days: int = 7) -> Dict:
        """
        分析来源分布

        Args:
            days: 统计最近多少天

        Returns:
            分布统计 {total: int, by_source: [{source, count, percentage}]}
        """
        stats = self.db.get_stats_by_source(days)

        if not stats:
            return {"total": 0, "by_source": []}

        total = sum(item['count'] for item in stats)

        # 计算百分比
        by_source = [
            {
                "source": item['source'],
                "count": item['count'],
                "percentage": round(item['count'] / total * 100, 2) if total > 0 else 0
            }
            for item in stats
        ]

        return {
            "total": total,
            "by_source": by_source
        }

    def get_top_news(self, limit: int = 20, source: str = None) -> List[Dict]:
        """
        获取热门新闻（出现次数最多的）

        Args:
            limit: 返回条数
            source: 来源筛选（可选）

        Returns:
            热门新闻列表 [{title, source, count, first_seen, last_seen}]
        """
        # 从数据库获取新闻
        news_list, _ = self.db.get_news(
            limit=10000,  # 获取更多数据用于分析
            source=source
        )

        if not news_list:
            return []

        # 按标题统计出现次数
        title_stats = {}
        for news in news_list:
            title = news['title']
            source = news['source']
            crawled_at = news['crawled_at']

            key = f"{source}:{title}"

            if key not in title_stats:
                title_stats[key] = {
                    "title": title,
                    "source": source,
                    "count": 0,
                    "first_seen": crawled_at,
                    "last_seen": crawled_at,
                }

            title_stats[key]["count"] += 1

            # 更新首次和最后出现时间
            if crawled_at < title_stats[key]["first_seen"]:
                title_stats[key]["first_seen"] = crawled_at
            if crawled_at > title_stats[key]["last_seen"]:
                title_stats[key]["last_seen"] = crawled_at

        # 按出现次数排序，取前N个
        top_news = sorted(
            title_stats.values(),
            key=lambda x: x["count"],
            reverse=True
        )[:limit]

        return top_news

    def get_summary_stats(self, days: int = 7) -> Dict:
        """
        获取汇总统计信息

        Args:
            days: 统计最近多少天

        Returns:
            汇总统计 {total_news, total_sources, avg_daily, top_sources, hot_words}
        """
        # 获取新闻总数
        cutoff_date = datetime.now() - timedelta(days=days)
        news_list, _ = self.db.get_news(limit=100000)
        filtered_news = [
            n for n in news_list
            if datetime.fromisoformat(n['crawled_at']) >= cutoff_date
        ]

        total_news = len(filtered_news)

        # 获取来源列表
        sources = self.db.get_all_sources()
        total_sources = len(sources)

        # 计算日均新闻数
        avg_daily = round(total_news / days, 2) if days > 0 else 0

        # 获取热门来源
        top_sources = self.db.get_stats_by_source(days)[:5]

        # 获取热词
        hot_words = self.extract_hot_words(days=days, top_n=10)

        return {
            "total_news": total_news,
            "total_sources": total_sources,
            "avg_daily": avg_daily,
            "top_sources": top_sources,
            "hot_words": hot_words,
        }
