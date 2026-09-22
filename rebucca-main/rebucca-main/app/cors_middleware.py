# -*- coding: utf-8 -*-
"""
轻量级 CORS 中间件（零第三方依赖）。

- 仅允许白名单来源（开发环境 Vite 默认 http://localhost:5173）
- 允许所有常用方法与请求头
- 允许携带 Cookie（sessionid / csrftoken）
- 直接应答 OPTIONS 预检请求

注意：允许凭证时 Access-Control-Allow-Origin 必须回显具体来源，不能为 *。
"""
from django.http import HttpResponse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

# 允许跨域访问的前端来源
ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
ALLOWED_HEADERS = "Content-Type, Authorization, Safe, X-CSRFToken, X-Requested-With"


class CorsMiddleware(MiddlewareMixin):
    """CORS 跨域支持。"""

    def process_request(self, request):
        # 预检请求直接返回，不走后续鉴权中间件
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin", "")
            if origin in ALLOWED_ORIGINS:
                response = HttpResponse(status=204)
                self._apply_headers(response, origin)
                return response
        return None

    def process_response(self, request, response):
        origin = request.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self._apply_headers(response, origin)
        return response

    @staticmethod
    def _apply_headers(response, origin):
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = ALLOWED_METHODS
        response["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
        response["Access-Control-Max-Age"] = "86400"
