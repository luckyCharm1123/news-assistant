# coding=utf-8
"""
鉴权模块
负责API密钥验证
"""

import os
from functools import wraps
from dotenv import load_dotenv
from flask import request, jsonify

# 加载环境变量
load_dotenv()


class AuthManager:
    """鉴权管理器"""

    def __init__(self):
        """初始化鉴权管理器"""
        self.api_key = os.getenv('API_KEY', '')
        if not self.api_key:
            raise ValueError("API_KEY 未在环境变量中设置")
        if self.api_key == 'your_secure_api_key_here_please_change_this_to_a_strong_password_2024':
            print("⚠️  警告: 使用默认API密钥，请在.env文件中修改为强密码！")

    def verify_key(self, api_key):
        """
        验证API密钥

        Args:
            api_key: 待验证的API密钥

        Returns:
            是否验证通过
        """
        return api_key == self.api_key

    def extract_key_from_request(self, request):
        """
        从请求中提取API密钥

        优先级：
        1. Header: X-API-Key
        2. Header: Authorization: Bearer <token>
        3. Query Param: api_key

        Args:
            request: Flask请求对象

        Returns:
            提取的API密钥或None
        """
        # 1. 从 X-API-Key header 获取
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return api_key

        # 2. 从 Authorization header 获取 (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # 去掉 "Bearer " 前缀

        # 3. 从 query parameter 获取
        api_key = request.args.get('api_key')
        if api_key:
            return api_key

        return None


# 全局鉴权管理器实例
auth_manager = AuthManager()


def require_auth(f):
    """
    装饰器：要求API密钥鉴权

    使用方法：
    @app.route('/api/protected')
    @require_auth
    def protected_route():
        return jsonify({'message': 'Authenticated'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 提取API密钥
        api_key = auth_manager.extract_key_from_request(request)

        if not api_key:
            return jsonify({
                'success': False,
                'error': '缺少API密钥，请在请求头中提供 X-API-Key 或 Authorization: Bearer <token>'
            }), 401

        # 验证API密钥
        if not auth_manager.verify_key(api_key):
            return jsonify({
                'success': False,
                'error': 'API密钥无效'
            }), 403

        # 鉴权通过，执行原函数
        return f(*args, **kwargs)

    return decorated_function


def check_auth_optional(f):
    """
    装饰器：可选的API密钥鉴权
    如果提供了密钥则验证，否则继续执行

    使用方法：
    @app.route('/api/public')
    @check_auth_optional
    def public_route():
        return jsonify({'message': 'Success'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 提取API密钥
        api_key = auth_manager.extract_key_from_request(request)

        # 如果提供了密钥，则需要验证
        if api_key and not auth_manager.verify_key(api_key):
            return jsonify({
                'success': False,
                'error': 'API密钥无效'
            }), 403

        # 继续执行原函数
        return f(*args, **kwargs)

    return decorated_function
