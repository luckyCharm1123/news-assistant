# coding=utf-8
"""
Flask Web应用 - 精简版
仅提供核心新闻查询API
"""

import logging
from datetime import datetime
from flask import Flask, jsonify, request

from ..database import DatabaseManager


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

    # 初始化数据库
    db_config = config.get('database', {})
    db = DatabaseManager(
        db_path=db_config.get('path', 'data/hotnews.db'),
        retention_days=db_config.get('retention_days', 7)
    )

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

    @app.route('/health')
    def health():
        """健康检查"""
        return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

    return app
