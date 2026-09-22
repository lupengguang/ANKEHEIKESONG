# -*- coding: utf-8 -*-
"""
VLM 视觉理解客户端 — VLMClient。

- 配置从后端 .env 读取：VLM_API_KEY / VLM_BASE_URL / VLM_MODEL
- understand_scene(frame)：
    帧 → base64 → OpenAI 兼容 chat/completions（qwen-vl 等）→ 解析 JSON dict
- VLM_API_KEY 未配置或调用失败时：自动降级为本地运动启发式分析（mock），
  保证无外网/无 key 时演示链路依然可跑（日志会明确标注降级）。

返回结构：
  {"has_person": bool, "direction": "approaching/leaving/unknown",
   "age_group": "adult/elder/child/unknown", "source": "vlm/mock",
   "raw": str, "error": str(可选)}
"""
import base64
import json
import logging
import os
import time
from pathlib import Path

import cv2

logger = logging.getLogger("services.vlm_client")

# 内置分析 Prompt
SCENE_PROMPT = """这是家庭门口监控画面。请分析：
1. 画面里有人吗？
2. 人是往门走还是离开？
3. 大概年龄？（成人/老人/小孩）

只返回JSON：
{"has_person": true/false, "direction": "approaching/leaving", "age_group": "adult/elder/child"}
"""

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-vl-max"


def load_env_file():
    """极简 .env 加载器（无第三方依赖），只对进程中不存在的键生效。"""
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    except Exception as e:
        logger.warning("读取 .env 失败: %s", e)


class VLMClient:
    """OpenAI 兼容视觉模型客户端，带本地降级。"""

    # 运动像素占画面比例超过该值才判定"有人"（经验值，抗摄像头噪声）
    PERSON_AREA_RATIO = 0.04

    def __init__(self, api_key=None, base_url=None, model=None):
        load_env_file()
        self.api_key = api_key or os.environ.get("VLM_API_KEY", "").strip()
        # 兼容“在这里填你的key”这类占位值
        if self.api_key.startswith("在这里"):
            self.api_key = ""
        self.base_url = (base_url or os.environ.get("VLM_BASE_URL")
                         or DEFAULT_BASE_URL).strip()
        self.model = model or os.environ.get("VLM_MODEL") or DEFAULT_MODEL

        # 本地降级分析的背景/状态
        self._bg_gray = None
        self._prev_motion_area = 0.0
        self._approach_streak = 0  # 连续"靠近"帧计数（确认机制，防噪声误报）

        if self.api_key:
            logger.info("VLMClient 初始化 model=%s base_url=%s",
                        self.model, self.base_url)
        else:
            logger.warning("VLM_API_KEY 未配置，understand_scene 将使用"
                           "本地运动启发式分析（mock 降级）")

    # ----------------------- 主入口 -----------------------

    def understand_scene(self, frame):
        """理解一帧画面，返回解析后的 dict。任何异常都不抛出。"""
        if frame is None:
            return self._result(False, "unknown", "unknown", source="mock",
                                error="frame 为空")
        if self.api_key:
            try:
                return self._call_vlm(frame)
            except Exception as e:
                logger.warning("VLM 调用失败，降级本地分析: %s", e)
                result = self._mock_analyze(frame)
                result["error"] = f"vlm failed: {e}"
                return result
        return self._mock_analyze(frame)

    # ----------------------- 真实 VLM 调用 -----------------------

    def _call_vlm(self, frame):
        """调用 OpenAI 兼容 chat/completions 接口。"""
        b64 = self.encode_frame(frame)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": SCENE_PROMPT},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }]

        t0 = time.time()
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            completion = client.chat.completions.create(
                model=self.model, messages=messages,
                temperature=0.1, max_tokens=300,
            )
            content = completion.choices[0].message.content
        except ImportError:
            # 无 openai SDK 时用 requests 直连
            import requests
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages,
                      "temperature": 0.1, "max_tokens": 300},
                timeout=15,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        data = self.parse_json(content)
        logger.info("VLM 分析完成 耗时%.1fs result=%s",
                    time.time() - t0, data)
        return self._result(
            bool(data.get("has_person", False)),
            str(data.get("direction", "unknown")),
            str(data.get("age_group", "unknown")),
            source="vlm", raw=content,
        )

    # ----------------------- 本地降级分析（mock） -----------------------

    def _mock_analyze(self, frame):
        """基于帧间运动的启发式分析：强运动 → 判定有人靠近（成人）。"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # 分辨率变化（重新开摄像头）时重置背景
        if self._bg_gray is not None \
                and self._bg_gray.shape[:2] != gray.shape[:2]:
            self._bg_gray = None

        if self._bg_gray is None:
            # accumulateWeighted 要求背景为 32 位浮点
            self._bg_gray = gray.astype("float32")
            return self._result(False, "unknown", "unknown", source="mock")

        # 浮点背景转回 uint8 再与当前帧做差
        diff = cv2.absdiff(cv2.convertScaleAbs(self._bg_gray), gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        changed = cv2.countNonZero(thresh) / float(thresh.size)
        # 缓慢更新背景，避免长时间静止的人变成背景
        cv2.accumulateWeighted(gray, self._bg_gray, 0.05)

        # 画面变化需达到足够面积才算"有人"（过滤摄像头噪声/光影抖动）
        person = changed > self.PERSON_AREA_RATIO
        # 运动面积明显增大才算"靠近"，相等/波动不算
        growing = changed > self._prev_motion_area * 1.2 \
            and changed > self.PERSON_AREA_RATIO
        self._prev_motion_area = changed

        direction = "unknown"
        if person and growing:
            self._approach_streak += 1
            # 连续两帧确认，避免单次噪声触发迎宾
            if self._approach_streak >= 2:
                direction = "approaching"
        else:
            self._approach_streak = 0

        result = self._result(person and direction == "approaching",
                              direction,
                              "adult" if direction == "approaching"
                              else "unknown", source="mock")
        if direction == "approaching":
            logger.info("[mock] 确认人员靠近 变化占比=%.3f", changed)
        return result

    def reset_background(self):
        """重置背景模型（摄像头重新启动时调用）。"""
        self._bg_gray = None
        self._prev_motion_area = 0.0
        self._approach_streak = 0

    # ----------------------- 工具方法 -----------------------

    @staticmethod
    def encode_frame(frame, jpeg_quality=80):
        """把 BGR numpy 帧编码为 base64 字符串。"""
        ok, buf = cv2.imencode(
            ".jpg", frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)])
        if not ok:
            raise RuntimeError("帧 JPEG 编码失败")
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    @staticmethod
    def parse_json(content):
        """从模型输出中提取 JSON（兼容 ```json 代码块与前后多余文字）。"""
        text = str(content).strip()
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                candidate = part.replace("json", "", 1).strip()
                if candidate.startswith("{"):
                    text = candidate
                    break
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        try:
            return json.loads(text)
        except Exception:
            logger.warning("无法解析 VLM JSON 输出: %s", content)
            return {}

    @staticmethod
    def _result(has_person, direction, age_group, source,
                raw="", error=""):
        valid_dir = {"approaching", "leaving"}
        valid_age = {"adult", "elder", "child"}
        return {
            "has_person": bool(has_person),
            "direction": direction if direction in valid_dir else "unknown",
            "age_group": age_group if age_group in valid_age else "unknown",
            "source": source,
            "raw": raw,
            "error": error,
        }
