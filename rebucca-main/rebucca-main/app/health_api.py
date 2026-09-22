# -*- coding: utf-8 -*-
"""
健康检查与接口文档视图。

路由：
  GET /api/health   健康检查（免登录）
  GET /openapi.json OpenAPI 3.0 描述（免登录）
  GET /docs         Swagger UI（免登录）
  GET /redoc        ReDoc（免登录）
"""
import json
import logging

from django.http import HttpResponse

from app.openapi_schema import build_openapi

logger = logging.getLogger("api.system")

# 服务版本（健康检查返回）
SERVICE_VERSION = "1.0.0"


def health(request):
    """GET /api/health — 健康检查。"""
    return HttpResponse(json.dumps({
        "code": 200,
        "message": "ok",
        "data": {
            "status": "running",
            "version": SERVICE_VERSION,
        },
    }), content_type="application/json")


def openapi_json(request):
    """GET /openapi.json — 返回 OpenAPI 规范 JSON。"""
    return HttpResponse(json.dumps(build_openapi()),
                        content_type="application/json")


def swagger_docs(request):
    """GET /docs — Swagger UI 页面（CDN 加载，规格取 /openapi.json）。"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>eufy AI HomeCare - Swagger</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css"/>
  <style>body{margin:0}.topbar{display:none}</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function () {
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis],
        layout: 'BaseLayout'
      });
    };
  </script>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def redoc_docs(request):
    """GET /redoc — ReDoc 页面（CDN 加载，规格取 /openapi.json）。"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>eufy AI HomeCare - ReDoc</title>
  <style>body{margin:0}</style>
</head>
<body>
  <redoc spec-url='/openapi.json'></redoc>
  <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")
