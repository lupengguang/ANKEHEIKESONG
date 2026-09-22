# -*- coding: utf-8 -*-
"""
OpenAPI 3.0 接口描述（手工维护，与 app/urls.py 实际路由保持一致）。

供 /docs（Swagger UI）与 /redoc 渲染。后端未使用 DRF，因此采用手工清单，
新增路由时请同步在此登记。
"""


def _unified_response(description="统一响应", data_ref=None):
    schema = {
        "type": "object",
        "properties": {
            "code": {"type": "integer", "example": 200},
            "message": {"type": "string", "example": "success"},
        },
    }
    if data_ref:
        schema["properties"]["data"] = {"$ref": data_ref}
    else:
        schema["properties"]["data"] = {"type": "object"}
    return {"description": description, "content": {"application/json": {"schema": schema}}}


def build_openapi():
    """返回 OpenAPI 3.0 规范 dict。"""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "eufy AI HomeCare API",
            "description": "Rebucca 智能看护后端接口文档（设备/中枢大脑/户外/室内/无网场景）",
            "version": "1.0.0",
        },
        "servers": [{"url": "http://localhost:8000", "description": "本地开发环境"}],
        "tags": [
            {"name": "系统", "description": "健康检查与文档"},
            {"name": "设备联动", "description": "设备注册、状态、PTZ/灯光/音频控制"},
            {"name": "中枢大脑", "description": "跨摄像头事件与轨迹"},
            {"name": "户外场景", "description": "迎宾/入侵防御"},
            {"name": "室内场景", "description": "宠物/老人/儿童/夜间模式"},
            {"name": "无网场景", "description": "4G 入侵/动物/低带宽/补传"},
        ],
        "paths": _build_paths(),
    }


def _build_paths():
    ok = lambda desc="成功响应": _unified_response(desc)
    paths = {}

    # ---------------- 系统 ----------------
    paths["/api/health"] = {
        "get": {
            "tags": ["系统"], "summary": "健康检查",
            "responses": {
                "200": {
                    "description": "服务运行状态",
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 200},
                            "message": {"type": "string", "example": "ok"},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "status": {"example": "running"},
                                    "version": {"example": "1.0.0"},
                                },
                            },
                        },
                    }}},
                },
            },
        },
    }

    # ---------------- 设备联动 ----------------
    dev_param = {"name": "device_id", "in": "path", "required": True,
                 "schema": {"type": "string"}, "description": "设备唯一标识"}
    paths.update({
        "/api/devices": {
            "get": {"tags": ["设备联动"], "summary": "设备列表",
                    "parameters": [
                        {"name": "type", "in": "query", "schema": {"type": "string"}},
                        {"name": "status", "in": "query", "schema": {"type": "string"}}],
                    "responses": {"200": ok()}},
        },
        "/api/devices/register": {
            "post": {"tags": ["设备联动"], "summary": "注册/更新设备",
                     "responses": {"200": ok()}},
        },
        "/api/devices/commands": {
            "get": {"tags": ["设备联动"], "summary": "命令历史",
                    "parameters": [
                        {"name": "device_id", "in": "query", "schema": {"type": "string"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}}],
                    "responses": {"200": ok()}},
        },
        "/api/devices/{device_id}/status": {
            "get": {"tags": ["设备联动"], "summary": "设备状态",
                    "parameters": [dev_param], "responses": {"200": ok()}},
        },
        "/api/devices/{device_id}/ptz": {
            "post": {"tags": ["设备联动"], "summary": "PTZ 控制",
                     "parameters": [dev_param], "responses": {"200": ok()}},
        },
        "/api/devices/{device_id}/light": {
            "post": {"tags": ["设备联动"], "summary": "灯光控制",
                     "parameters": [dev_param], "responses": {"200": ok()}},
        },
        "/api/devices/{device_id}/audio": {
            "post": {"tags": ["设备联动"], "summary": "播放音频",
                     "parameters": [dev_param], "responses": {"200": ok()}},
        },
        "/api/devices/{device_id}/cross-track": {
            "post": {"tags": ["设备联动"], "summary": "跨摄像头联动（防抖）",
                     "parameters": [dev_param], "responses": {"200": ok()}},
        },
    })

    # ---------------- 中枢大脑 ----------------
    paths.update({
        "/api/brain/events": {
            "get": {"tags": ["中枢大脑"], "summary": "事件查询",
                    "responses": {"200": ok()}},
        },
        "/api/brain/tracks": {
            "get": {"tags": ["中枢大脑"], "summary": "跨摄像头轨迹",
                    "parameters": [
                        {"name": "track_id", "in": "query", "required": True,
                         "schema": {"type": "string"}}],
                    "responses": {"200": ok()}},
        },
        "/api/brain/search": {
            "post": {"tags": ["中枢大脑"], "summary": "自然语言搜索",
                     "responses": {"200": ok()}},
        },
        "/api/brain/weekly-report": {
            "get": {"tags": ["中枢大脑"], "summary": "周报数据",
                    "responses": {"200": ok()}},
        },
        "/api/brain/generate-report": {
            "post": {"tags": ["中枢大脑"], "summary": "生成报告",
                     "responses": {"200": ok()}},
        },
    })

    # ---------------- 户外场景 ----------------
    paths.update({
        "/api/outdoor/config": {
            "get": {"tags": ["户外场景"], "summary": "查询场景配置",
                    "responses": {"200": ok()}},
        },
        "/api/outdoor/config-update": {
            "put": {"tags": ["户外场景"], "summary": "更新场景配置",
                    "responses": {"200": ok()}},
        },
        "/api/outdoor/trigger-welcome": {
            "post": {"tags": ["户外场景"], "summary": "触发迎宾",
                     "responses": {"200": ok()}},
        },
        "/api/outdoor/trigger-intrusion": {
            "post": {"tags": ["户外场景"], "summary": "触发入侵防御",
                     "responses": {"200": ok()}},
        },
        "/api/outdoor/events": {
            "get": {"tags": ["户外场景"], "summary": "事件查询",
                    "responses": {"200": ok()}},
        },
    })

    # ---------------- 室内场景 ----------------
    paths.update({
        "/api/indoor/config": {
            "get": {"tags": ["室内场景"], "summary": "查询室内配置",
                    "responses": {"200": ok()}},
            "put": {"tags": ["室内场景"], "summary": "更新室内配置（热更新）",
                    "responses": {"200": ok()}},
        },
        "/api/indoor/test-pet": {
            "post": {"tags": ["室内场景"], "summary": "测试宠物模式",
                     "responses": {"200": ok()}},
        },
        "/api/indoor/test-elder": {
            "post": {"tags": ["室内场景"], "summary": "测试老人模式",
                     "responses": {"200": ok()}},
        },
        "/api/indoor/events": {
            "get": {"tags": ["室内场景"], "summary": "室内事件查询",
                    "responses": {"200": ok()}},
        },
    })

    # ---------------- 无网场景 ----------------
    paths.update({
        "/api/offline/config": {
            "get": {"tags": ["无网场景"], "summary": "查询无网配置",
                    "responses": {"200": ok()}},
            "put": {"tags": ["无网场景"], "summary": "更新无网配置（热更新）",
                    "responses": {"200": ok()}},
        },
        "/api/offline/test-intrusion": {
            "post": {"tags": ["无网场景"], "summary": "测试入侵防御",
                     "responses": {"200": ok()}},
        },
        "/api/offline/events": {
            "get": {"tags": ["无网场景"], "summary": "无网事件查询",
                    "responses": {"200": ok()}},
        },
        "/api/offline/stats": {
            "get": {"tags": ["无网场景"], "summary": "流量与补传统计",
                    "responses": {"200": ok()}},
        },
        "/api/offline/replay": {
            "post": {"tags": ["无网场景"], "summary": "手动触发离线补传",
                     "responses": {"200": ok()}},
        },
    })

    return paths
