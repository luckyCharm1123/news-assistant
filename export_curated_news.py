#!/usr/bin/env python3
# coding=utf-8
"""
导出AI精选新闻到CSV文件
"""

import csv
import os
import sys
from datetime import datetime
from typing import List, Dict

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager


def export_curated_news_to_csv(
    db_path: str = 'data/hotnews.db',
    output_file: str = None,
    limit: int = None
) -> str:
    """
    导出AI精选新闻到CSV文件

    Args:
        db_path: 数据库文件路径
        output_file: 输出CSV文件路径（默认自动生成）
        limit: 导出条数限制（None表示全部）

    Returns:
        CSV文件路径
    """
    # 检查数据库是否存在
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None

    # 初始化数据库管理器
    db = DatabaseManager(db_path)

    # 获取总数
    total_count = db.get_curated_news_count()
    print(f"📊 数据库中共有 {total_count} 条AI精选新闻")

    if total_count == 0:
        print("⚠️  没有数据可以导出")
        return None

    # 获取数据
    limit = limit or total_count
    news_list = db.get_all_curated_news(limit=limit)

    print(f"✅ 成功读取 {len(news_list)} 条记录")

    # 生成输出文件名
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'curated_news_{timestamp}.csv'

    # 导出CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 写入表头
            headers = [
                'ID',
                'AI精选标题',
                '摘要',
                '原始新闻ID',
                '原始新闻标题',
                '来源',
                'URL',
                '创建时间',
                '更新时间'
            ]
            writer.writerow(headers)

            # 写入数据
            for news in news_list:
                row = [
                    news.get('id'),
                    news.get('title'),
                    news.get('summary') or '',
                    news.get('source_news_id'),
                    news.get('original_title') or '',
                    news.get('source') or '',
                    news.get('url') or '',
                    news.get('created_at'),
                    news.get('updated_at')
                ]
                writer.writerow(row)

        print(f"📁 CSV文件已保存到: {output_file}")
        print(f"📄 文件大小: {os.path.getsize(output_file)} 字节")

        return output_file

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None


def export_with_source_news(
    db_path: str = 'data/hotnews.db',
    output_file: str = None,
    limit: int = None
) -> str:
    """
    导出AI精选新闻（包含所有相关的原始新闻）

    Args:
        db_path: 数据库文件路径
        output_file: 输出CSV文件路径
        limit: 导出条数限制

    Returns:
        CSV文件路径
    """
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None

    db = DatabaseManager(db_path)
    total_count = db.get_curated_news_count()

    print(f"📊 数据库中共有 {total_count} 条AI精选新闻")

    if total_count == 0:
        print("⚠️  没有数据可以导出")
        return None

    # 获取数据
    limit = limit or total_count
    news_list = db.get_all_curated_news(limit=limit)

    print(f"✅ 成功读取 {len(news_list)} 条记录")

    # 生成输出文件名
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'curated_news_detailed_{timestamp}.csv'

    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 写入表头（详细版）
            headers = [
                'AI精选ID',
                'AI精选标题',
                '摘要',
                '原始新闻ID',
                '原始新闻标题',
                '来源',
                'URL',
                '爬取时间',
                'AI精选创建时间',
                'AI精选更新时间'
            ]
            writer.writerow(headers)

            # 写入数据
            for news in news_list:
                row = [
                    news.get('id'),
                    news.get('title'),
                    news.get('summary') or '',
                    news.get('source_news_id'),
                    news.get('original_title') or '',
                    news.get('source') or '',
                    news.get('url') or '',
                    news.get('crawled_at') or '',
                    news.get('created_at'),
                    news.get('updated_at')
                ]
                writer.writerow(row)

        print(f"📁 CSV文件已保存到: {output_file}")
        print(f"📄 文件大小: {os.path.getsize(output_file)} 字节")

        return output_file

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='导出AI精选新闻到CSV文件')
    parser.add_argument(
        '--db',
        default='data/hotnews.db',
        help='数据库文件路径（默认: data/hotnews.db）'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出CSV文件路径（默认自动生成）'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='导出条数限制（默认全部）'
    )
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='导出详细版本（包含更多信息）'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("AI精选新闻导出工具")
    print("=" * 60)
    print()

    if args.detailed:
        output_file = export_with_source_news(
            db_path=args.db,
            output_file=args.output,
            limit=args.limit
        )
    else:
        output_file = export_curated_news_to_csv(
            db_path=args.db,
            output_file=args.output,
            limit=args.limit
        )

    if output_file:
        print()
        print("✅ 导出完成！")
        print(f"📂 文件路径: {os.path.abspath(output_file)}")
    else:
        print()
        print("❌ 导出失败")
        sys.exit(1)
