# coding=utf-8
"""
Flask Web应用
提供新闻查询、搜索和统计功能
"""

import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request

from ..database import DatabaseManager
from ..analyzer import NewsAnalyzer
from ..auth import require_auth


def create_app(config_path: str = "config/config.yaml"):
    """
    创建Flask应用

    Args:
        config_path: 配置文件路径

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)

    # 加载配置
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 初始化数据库和分析器
    db_config = config.get('database', {})
    db = DatabaseManager(
        db_path=db_config.get('path', 'data/hotnews.db'),
        retention_days=db_config.get('retention_days', 7)
    )
    analyzer = NewsAnalyzer(db)

    # ==================== 路由定义 ====================

    @app.route('/')
    def index():
        """首页"""
        try:
            # 获取最近24小时的新闻
            latest_news = db.get_latest_news(hours=24)

            # 按来源分组
            grouped_news = {}
            for news in latest_news:
                source = news['source']
                if source not in grouped_news:
                    grouped_news[source] = []
                grouped_news[source].append(news)

            # 获取统计信息
            summary = analyzer.get_summary_stats(days=1)

            # 获取AI精选新闻
            curated_news = db.get_all_curated_news(limit=20, offset=0)

            return render_template(
                'index.html',
                grouped_news=grouped_news,
                summary=summary,
                curated_news=curated_news,
                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            app.logger.error(f"首页加载失败: {e}")
            return render_template('index.html', grouped_news={}, summary={}, curated_news=[], error=str(e))

    @app.route('/search')
    def search():
        """搜索页"""
        try:
            # 获取所有来源
            sources = db.get_all_sources()

            return render_template('search.html', sources=sources)
        except Exception as e:
            app.logger.error(f"搜索页加载失败: {e}")
            return render_template('search.html', sources=[], error=str(e))

    @app.route('/stats')
    def stats():
        """统计页"""
        try:
            # 获取统计数据
            summary = analyzer.get_summary_stats(days=7)
            source_dist = analyzer.analyze_source_distribution(days=7)
            hourly_dist = analyzer.get_hourly_distribution(days=1)
            trend_data = analyzer.get_trend_data(days=7)

            return render_template(
                'stats.html',
                summary=summary,
                source_dist=source_dist,
                hourly_dist=hourly_dist,
                trend_data=trend_data
            )
        except Exception as e:
            app.logger.error(f"统计页加载失败: {e}")
            return render_template('stats.html', error=str(e))

    # ==================== API接口 ====================

    @app.route('/api/news')
    def api_news():
        """获取新闻列表API"""
        try:
            # 获取参数
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            source = request.args.get('source')
            keyword = request.args.get('keyword')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            # 查询数据
            news_list, total = db.get_news(
                limit=limit,
                offset=offset,
                source=source,
                keyword=keyword,
                start_date=start_date,
                end_date=end_date
            )

            return jsonify({
                'success': True,
                'data': news_list,
                'total': total,
                'limit': limit,
                'offset': offset
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/news/<int:news_id>')
    def api_news_detail(news_id):
        """获取新闻详情API"""
        try:
            news = db.get_news_by_id(news_id)
            if news:
                return jsonify({'success': True, 'data': news})
            else:
                return jsonify({'success': False, 'error': '新闻不存在'}), 404
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stats/hotwords')
    def api_stats_hotwords():
        """获取热词统计API"""
        try:
            days = int(request.args.get('days', 1))
            top_n = int(request.args.get('top_n', 50))
            hot_words = analyzer.extract_hot_words(days=days, top_n=top_n)
            return jsonify({'success': True, 'data': hot_words})
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stats/trend')
    def api_stats_trend():
        """获取趋势数据API"""
        try:
            days = int(request.args.get('days', 7))
            trend_data = analyzer.get_trend_data(days=days)
            return jsonify({'success': True, 'data': trend_data})
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stats/by_source')
    def api_stats_by_source():
        """按来源统计API"""
        try:
            days = int(request.args.get('days', 7))
            stats = analyzer.get_news_frequency(days=days)
            return jsonify({'success': True, 'data': stats})
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stats/summary')
    def api_stats_summary():
        """汇总统计API"""
        try:
            days = int(request.args.get('days', 7))
            summary = analyzer.get_summary_stats(days=days)
            return jsonify({'success': True, 'data': summary})
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stats/hourly')
    def api_stats_hourly():
        """每小时分布API"""
        try:
            days = int(request.args.get('days', 1))
            data = analyzer.get_hourly_distribution(days=days)
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/top_news')
    def api_top_news():
        """热门新闻API"""
        try:
            limit = int(request.args.get('limit', 20))
            source = request.args.get('source')
            top_news = analyzer.get_top_news(limit=limit, source=source)
            return jsonify({'success': True, 'data': top_news})
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/recent_news')
    def api_recent_news():
        """获取最近新增的新闻（简化版API）"""
        try:
            hours = int(request.args.get('hours', 2))
            news_list = db.get_recent_news_simple(hours=hours)
            return jsonify({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'hours': hours
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/news/<int:news_id>/decrease_popularity', methods=['POST'])
    @require_auth
    def api_decrease_popularity(news_id):
        """降低新闻关注度API（供MCP服务使用）- 需要鉴权"""
        try:
            # 获取参数
            data = request.get_json() or {}
            decrease_amount = int(data.get('decrease_amount', 1))

            # 降低关注度
            success = db.decrease_popularity(news_id, decrease_amount)

            if success:
                # 获取更新后的新闻信息
                news = db.get_news_by_id(news_id)
                return jsonify({
                    'success': True,
                    'message': f'新闻ID {news_id} 关注度已降低 {decrease_amount}',
                    'data': {
                        'id': news_id,
                        'title': news.get('title') if news else None,
                        'current_popularity': news.get('popularity') if news else None,
                        'decreased_by': decrease_amount
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'新闻ID {news_id} 不存在或降低失败'
                }), 404

        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/news/batch_decrease_popularity', methods=['POST'])
    @require_auth
    def api_batch_decrease_popularity():
        """批量降低新闻关注度API - 需要鉴权"""
        try:
            data = request.get_json() or {}
            news_ids = data.get('news_ids', [])
            decrease_amount = int(data.get('decrease_amount', 1))

            if not news_ids:
                return jsonify({
                    'success': False,
                    'error': 'news_ids 参数不能为空'
                }), 400

            results = []
            for news_id in news_ids:
                success = db.decrease_popularity(news_id, decrease_amount)
                results.append({
                    'id': news_id,
                    'success': success
                })

            success_count = sum(1 for r in results if r['success'])

            return jsonify({
                'success': True,
                'message': f'成功降低 {success_count}/{len(news_ids)} 条新闻的关注度',
                'data': {
                    'total': len(news_ids),
                    'success_count': success_count,
                    'failed_count': len(news_ids) - success_count,
                    'results': results
                }
            })

        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/news/high_popularity', methods=['GET'])
    def api_high_popularity_news():
        """获取高关注度新闻API"""
        try:
            limit = int(request.args.get('limit', 20))
            min_popularity = int(request.args.get('min_popularity', 3))

            with db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM news
                    WHERE popularity >= ?
                    ORDER BY popularity DESC, crawled_at DESC
                    LIMIT ?
                """, (min_popularity, limit))

                news_list = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'min_popularity': min_popularity
            })

        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/health')
    def health():
        """健康检查"""
        return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

    # ==================== AI精选新闻 API接口 ====================

    @app.route('/api/curated_news', methods=['GET'])
    def api_curated_news_list():
        """获取AI精选新闻列表API"""
        try:
            # 支持获取所有记录的参数
            limit_param = request.args.get('limit', '100')

            # 处理特殊的 limit 参数
            if limit_param == 'all' or limit_param == '0' or limit_param == '':
                # 获取所有记录，设置一个超大值
                limit = 999999
            else:
                try:
                    limit = int(limit_param)
                    # 防止负数
                    if limit < 0:
                        limit = 100
                except (ValueError, TypeError):
                    limit = 100

            offset = int(request.args.get('offset', 0))

            curated_list = db.get_all_curated_news(limit=limit, offset=offset)
            total = db.get_curated_news_count()

            return jsonify({
                'success': True,
                'data': curated_list,
                'total': total,
                'limit': limit if limit != 999999 else 'all',
                'offset': offset
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/<int:curated_id>', methods=['GET'])
    def api_curated_news_detail(curated_id):
        """获取单条AI精选新闻详情API"""
        try:
            news = db.get_curated_news_by_id(curated_id)
            if news:
                return jsonify({'success': True, 'data': news})
            else:
                return jsonify({'success': False, 'error': 'AI精选新闻不存在'}), 404
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news', methods=['POST'])
    @require_auth
    def api_create_curated_news():
        """创建或更新AI精选新闻API（用于n8n工作流）"""
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            source_news_id = data.get('source_news_id')
            summary = data.get('summary')

            if not title or not source_news_id:
                return jsonify({
                    'success': False,
                    'error': 'title和source_news_id为必填字段'
                }), 400

            # 检查原始新闻是否存在
            original_news = db.get_news_by_id(source_news_id)
            if not original_news:
                return jsonify({
                    'success': False,
                    'error': f'原始新闻ID {source_news_id} 不存在'
                }), 404

            # 插入或更新
            curated_id = db.insert_or_update_curated_news(
                title=title,
                source_news_id=source_news_id,
                summary=summary
            )

            # 获取完整记录
            curated_news = db.get_curated_news_by_id(curated_id)

            return jsonify({
                'success': True,
                'message': f'AI精选新闻已创建/更新',
                'data': curated_news
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/batch', methods=['POST'])
    @require_auth
    def api_batch_create_curated_news():
        """批量创建或更新AI精选新闻API（用于n8n工作流）"""
        try:
            data = request.get_json()
            news_list = data.get('news_list', [])

            # 处理 news_list 参数 - 可能是 JSON 字符串或列表
            if isinstance(news_list, str):
                try:
                    import json
                    news_list = json.loads(news_list)
                except json.JSONDecodeError as e:
                    return jsonify({
                        'success': False,
                        'error': f'news_list JSON 解析失败: {str(e)}'
                    }), 400

            if not news_list:
                return jsonify({
                    'success': False,
                    'error': 'news_list不能为空'
                }), 400

            inserted, updated = db.batch_insert_curated_news(news_list)

            return jsonify({
                'success': True,
                'message': f'批量操作完成: 新增{inserted}条, 更新{updated}条',
                'data': {
                    'inserted_count': inserted,
                    'updated_count': updated,
                    'total_count': inserted + updated
                }
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/<int:curated_id>/summary', methods=['PUT'])
    @require_auth
    def api_update_curated_summary(curated_id):
        """更新AI精选新闻摘要API（用于n8n工作流）"""
        try:
            data = request.get_json()
            summary = data.get('summary', '').strip()

            if not summary:
                return jsonify({
                    'success': False,
                    'error': 'summary为必填字段'
                }), 400

            success = db.update_curated_news_summary(curated_id, summary)

            if success:
                # 获取更新后的记录
                curated_news = db.get_curated_news_by_id(curated_id)
                return jsonify({
                    'success': True,
                    'message': f'AI精选新闻 ID={curated_id} 摘要已更新',
                    'data': curated_news
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'AI精选新闻 ID={curated_id} 不存在'
                }), 404
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/<int:curated_id>', methods=['DELETE'])
    @require_auth
    def api_delete_curated_news(curated_id):
        """删除AI精选新闻API"""
        try:
            success = db.delete_curated_news(curated_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': f'AI精选新闻 ID={curated_id} 已删除'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'AI精选新闻 ID={curated_id} 不存在'
                }), 404
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/check', methods=['POST'])
    @require_auth
    def api_check_curated_news():
        """检查AI精选新闻标题是否已存在API"""
        try:
            data = request.get_json()
            title = data.get('title', '').strip()

            if not title:
                return jsonify({
                    'success': False,
                    'error': 'title为必填字段'
                }), 400

            existing = db.check_curated_news_exists(title)

            if existing:
                return jsonify({
                    'success': True,
                    'exists': True,
                    'data': existing
                })
            else:
                return jsonify({
                    'success': True,
                    'exists': False,
                    'data': None
                })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # ==================== 新闻合并 API接口 ====================

    @app.route('/api/curated_news/active', methods=['GET'])
    def api_get_active_curated_news():
        """获取未被合并的AI精选新闻API"""
        try:
            limit = int(request.args.get('limit', 100))
            active_news = db.get_active_curated_news(limit=limit)

            return jsonify({
                'success': True,
                'data': active_news,
                'count': len(active_news)
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/batch_get', methods=['POST'])
    def api_batch_get_curated_news():
        """批量获取AI精选新闻详情API"""
        try:
            data = request.get_json()
            news_ids = data.get('news_ids', [])

            if not news_ids:
                return jsonify({
                    'success': False,
                    'error': 'news_ids 参数不能为空'
                }), 400

            news_list = db.get_curated_news_for_merging(news_ids)

            return jsonify({
                'success': True,
                'data': news_list,
                'count': len(news_list)
            })
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/curated_news/merge', methods=['POST'])
    @require_auth
    def api_merge_curated_news():
        """合并AI精选新闻API"""
        try:
            data = request.get_json()
            keep_id = data.get('keep_id')
            merge_ids = data.get('merge_ids', [])
            merged_title = data.get('merged_title', '').strip()
            merged_summary = data.get('merged_summary')

            if not keep_id or not merge_ids or not merged_title:
                return jsonify({
                    'success': False,
                    'error': 'keep_id, merge_ids, merged_title 为必填字段'
                }), 400

            # 执行合并
            success = db.merge_curated_news(
                keep_id=keep_id,
                merge_ids=merge_ids,
                merged_title=merged_title,
                merged_summary=merged_summary
            )

            if success:
                return jsonify({
                    'success': True,
                    'message': f'成功合并 {len(merge_ids)} 条新闻到 ID {keep_id}',
                    'data': {
                        'keep_id': keep_id,
                        'merged_count': len(merge_ids),
                        'merged_ids': merge_ids
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '合并失败'
                }), 500
        except Exception as e:
            app.logger.error(f"API错误: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return app
