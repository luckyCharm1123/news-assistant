# coding=utf-8
"""
数据库模块
负责SQLite数据库的创建、数据插入、查询和清理
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager


# 数据库表结构
CREATE_TABLES_SQL = """
-- 新闻表
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    rank INTEGER,
    popularity INTEGER DEFAULT 0,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- URL去重索引（优先）
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url
    ON news(url) WHERE url IS NOT NULL AND url != '';

-- 标题去重索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_title
    ON news(title);

-- 爬取时间索引（用于查询和清理）
CREATE INDEX IF NOT EXISTS idx_news_crawled_at ON news(crawled_at);

-- 来源索引（用于统计）
CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);

-- 关注度索引（用于热门排序）
CREATE INDEX IF NOT EXISTS idx_news_popularity ON news(popularity DESC);
"""


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str, retention_days: int = 7):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
            retention_days: 数据保留天数
        """
        self.db_path = db_path
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)

        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 初始化数据库
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            self.logger.info(f"数据库初始化完成: {self.db_path}")

    def insert_news(self, news_list: List[Dict]) -> int:
        """
        批量插入新闻数据（URL和标题双重去重）

        去重逻辑：
        1. 如果URL存在且不为空，按URL去重
        2. 如果标题存在，按标题去重
        3. 重复时关注度+1，更新爬取时间

        Args:
            news_list: 新闻列表，每项包含 {title, source, url, rank}

        Returns:
            成功插入的条数
        """
        if not news_list:
            return 0

        inserted_count = 0
        updated_count = 0

        with self._get_connection() as conn:
            for news in news_list:
                title = news.get('title', '').strip()
                source = news.get('source', '').strip()
                url = news.get('url', '').strip()
                rank = news.get('rank')

                # 验证必填字段
                if not title or not source:
                    self.logger.warning(f"跳过无效数据: title={title}, source={source}")
                    continue

                try:
                    current_time = datetime.now()

                    # 优先使用URL去重，其次使用标题去重
                    if url and url != '':
                        # URL去重：检查URL是否已存在
                        cursor = conn.execute("""
                            SELECT id FROM news WHERE url = ?
                        """, (url,))

                        existing = cursor.fetchone()

                        if existing:
                            # URL存在，更新关注度+1，更新爬取时间
                            conn.execute("""
                                UPDATE news
                                SET popularity = popularity + 1,
                                    crawled_at = ?,
                                    source = ?,
                                    rank = ?
                                WHERE id = ?
                            """, (current_time, source, rank, existing[0]))
                            updated_count += 1
                        else:
                            # URL不存在，检查标题是否已存在
                            cursor = conn.execute("""
                                SELECT id FROM news WHERE title = ?
                            """, (title,))

                            existing = cursor.fetchone()

                            if existing:
                                # 标题存在，更新关注度+1，更新爬取时间
                                conn.execute("""
                                    UPDATE news
                                    SET popularity = popularity + 1,
                                        crawled_at = ?,
                                        source = ?,
                                        rank = ?,
                                        url = ?
                                    WHERE id = ?
                                """, (current_time, source, rank, url, existing[0]))
                                updated_count += 1
                            else:
                                # 新数据，插入
                                conn.execute("""
                                    INSERT INTO news (title, source, url, rank, popularity, crawled_at)
                                    VALUES (?, ?, ?, ?, 1, ?)
                                """, (title, source, url, rank, current_time))
                                inserted_count += 1
                    else:
                        # 无URL，仅按标题去重
                        cursor = conn.execute("""
                            SELECT id FROM news WHERE title = ?
                        """, (title,))

                        existing = cursor.fetchone()

                        if existing:
                            # 标题存在，更新关注度+1，更新爬取时间
                            conn.execute("""
                                UPDATE news
                                SET popularity = popularity + 1,
                                    crawled_at = ?,
                                    source = ?,
                                    rank = ?
                                WHERE id = ?
                            """, (current_time, source, rank, existing[0]))
                            updated_count += 1
                        else:
                            # 新数据，插入
                            conn.execute("""
                                INSERT INTO news (title, source, url, rank, popularity, crawled_at)
                                VALUES (?, ?, ?, ?, 1, ?)
                            """, (title, source, None, rank, current_time))
                            inserted_count += 1

                except sqlite3.Error as e:
                    self.logger.error(f"操作失败: {e}, title={title}, source={source}")

            self.logger.info(f"操作完成: 新增={inserted_count}, 更新关注度={updated_count}")

        return inserted_count

    def cleanup_old_data(self) -> int:
        """
        清理过期数据（删除retention_days天前的数据）

        Returns:
            删除的条数
        """
        if self.retention_days <= 0:
            self.logger.info("数据保留期为0，不进行清理")
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM news
                WHERE crawled_at < ?
            """, (cutoff_str,))

            deleted_count = cursor.rowcount
            self.logger.info(f"清理完成: 删除 {deleted_count} 条过期数据（早于 {cutoff_str}）")

        return deleted_count

    def get_news(
        self,
        limit: int = 100,
        offset: int = 0,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        查询新闻列表

        Args:
            limit: 返回条数
            offset: 偏移量
            source: 来源筛选
            keyword: 关键词搜索（标题）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            (新闻列表, 总数)
        """
        conditions = []
        params = []

        # 构建查询条件
        if source:
            conditions.append("source = ?")
            params.append(source)

        if keyword:
            conditions.append("title LIKE ?")
            params.append(f"%{keyword}%")

        if start_date:
            conditions.append("DATE(crawled_at) >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("DATE(crawled_at) <= ?")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        with self._get_connection() as conn:
            count_cursor = conn.execute(f"""
                SELECT COUNT(*) FROM news {where_clause}
            """, params)
            total = count_cursor.fetchone()[0]

            # 查询数据
            query = f"""
                SELECT * FROM news {where_clause}
                ORDER BY crawled_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            news_list = [dict(row) for row in rows]

        return news_list, total

    def get_news_by_id(self, news_id: int) -> Optional[Dict]:
        """
        根据ID获取单条新闻

        Args:
            news_id: 新闻ID

        Returns:
            新闻字典，不存在返回None
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_stats_by_source(self, days: int = 7) -> List[Dict]:
        """
        按来源统计新闻数量

        Args:
            days: 统计最近多少天

        Returns:
            统计列表 [{source, count}]
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM news
                WHERE crawled_at >= ?
                GROUP BY source
                ORDER BY count DESC
            """, (cutoff_date,))

            return [dict(row) for row in cursor.fetchall()]

    def get_news_count_by_hour(self, days: int = 1) -> List[Dict]:
        """
        按小时统计新闻数量

        Args:
            days: 统计最近多少天

        Returns:
            统计列表 [{hour, count}]
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    CAST(strftime('%H', crawled_at) AS INTEGER) as hour,
                    COUNT(*) as count
                FROM news
                WHERE crawled_at >= ?
                GROUP BY hour
                ORDER BY hour
            """, (cutoff_date,))

            return [dict(row) for row in cursor.fetchall()]

    def get_latest_news(self, hours: int = 24) -> List[Dict]:
        """
        获取最近的新闻

        Args:
            hours: 获取最近多少小时的新闻

        Returns:
            新闻列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM news
                WHERE crawled_at >= ?
                ORDER BY crawled_at DESC
            """, (cutoff_time,))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_news_simple(self, hours: int = 2) -> List[Dict]:
        """
        获取最近新增的新闻（简化版，仅包含ID和标题）

        Args:
            hours: 获取最近多少小时新增的新闻

        Returns:
            新闻列表，仅包含 id 和 title
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title FROM news
                WHERE crawled_at >= ?
                ORDER BY crawled_at DESC
            """, (cutoff_time,))

            return [dict(row) for row in cursor.fetchall()]

    def search_keywords(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        关键词搜索

        Args:
            keyword: 关键词
            limit: 返回条数

        Returns:
            新闻列表
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM news
                WHERE title LIKE ?
                ORDER BY crawled_at DESC
                LIMIT ?
            """, (f"%{keyword}%", limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_all_sources(self) -> List[str]:
        """获取所有来源列表"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT source FROM news ORDER BY source")
            return [row[0] for row in cursor.fetchall()]

    def decrease_popularity(self, news_id: int, decrease_amount: int = 1) -> bool:
        """
        降低新闻关注度

        Args:
            news_id: 新闻ID
            decrease_amount: 降低的数值，默认为1

        Returns:
            是否成功降低关注度
        """
        try:
            with self._get_connection() as conn:
                # 确保关注度不会小于0
                cursor = conn.execute("""
                    UPDATE news
                    SET popularity = CASE
                        WHEN popularity > ? THEN popularity - ?
                        ELSE 0
                    END
                    WHERE id = ?
                """, (decrease_amount, decrease_amount, news_id))

                if cursor.rowcount > 0:
                    # 获取更新后的关注度
                    result = conn.execute("SELECT popularity FROM news WHERE id = ?", (news_id,))
                    row = result.fetchone()
                    if row:
                        self.logger.info(f"新闻ID {news_id} 关注度已降低，当前关注度: {row[0]}")
                    return True
                else:
                    self.logger.warning(f"新闻ID {news_id} 不存在")
                    return False
        except Exception as e:
            self.logger.error(f"降低关注度失败: {e}")
            return False

    def get_news_by_ids(self, news_ids: List[int]) -> List[Dict]:
        """
        根据ID列表获取新闻

        Args:
            news_ids: 新闻ID列表

        Returns:
            新闻列表
        """
        if not news_ids:
            return []

        with self._get_connection() as conn:
            placeholders = ','.join('?' * len(news_ids))
            cursor = conn.execute(f"""
                SELECT * FROM news
                WHERE id IN ({placeholders})
                ORDER BY popularity DESC, crawled_at DESC
            """, news_ids)

            return [dict(row) for row in cursor.fetchall()]
