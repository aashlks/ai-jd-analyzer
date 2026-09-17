"""Offline tests for the DeepSeek JD analysis logic (no real API call)."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analyzer import DEFAULT_MODEL, analyze_jd
from models import JobAnalysis


SAMPLE_RESULT = JobAnalysis(
    job_title="内容运营专员",
    company="示例公司",
    employment_type="正式",
    location="武汉",
    responsibilities=["策划并发布内容"],
    required_skills=["文案写作", "数据复盘"],
    other_requirements=[],
    education_requirement="本科及以上",
    experience_requirement="1 年以上相关经验",
    work_schedule="未提及",
    bonus_points=["有账号运营经验"],
)


class FakeCompletions:
    """Remember the request and return prepared JSON content."""

    def __init__(self, content: str | None) -> None:
        message = SimpleNamespace(content=content)
        self.response = SimpleNamespace(
            choices=[SimpleNamespace(message=message)] if content is not None else []
        )
        self.last_request: dict | None = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return self.response


class FakeClient:
    def __init__(self, content: str | None) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


class AnalyzeJDTests(unittest.TestCase):
    def test_returns_validated_result_and_sends_jd(self) -> None:
        client = FakeClient(SAMPLE_RESULT.model_dump_json())

        result = analyze_jd(
            "招聘内容运营专员，要求文案写作和数据复盘能力",
            client=client,
            model="test-model",
        )

        self.assertEqual(result.job_title, "内容运营专员")
        request = client.chat.completions.last_request
        self.assertIsNotNone(request)
        self.assertEqual(request["model"], "test-model")
        self.assertEqual(request["response_format"], {"type": "json_object"})
        self.assertIn("招聘内容运营专员", request["messages"][1]["content"])
        self.assertIn("不要假设这是技术岗位", request["messages"][0]["content"])

    def test_uses_model_from_environment(self) -> None:
        client = FakeClient(SAMPLE_RESULT.model_dump_json())

        with patch.dict(os.environ, {"DEEPSEEK_MODEL": "model-from-env"}):
            analyze_jd("一段 JD", client=client)

        self.assertEqual(
            client.chat.completions.last_request["model"], "model-from-env"
        )

    def test_sends_all_attendance_details_with_explicit_instruction(self) -> None:
        client = FakeClient(SAMPLE_RESULT.model_dump_json())

        analyze_jd("每周到岗 4 天，连续实习 3 个月", client=client)

        messages = client.chat.completions.last_request["messages"]
        self.assertIn("出勤和时长要求", messages[0]["content"])
        self.assertIn("每周到岗 4 天", messages[1]["content"])
        self.assertIn("连续实习 3 个月", messages[1]["content"])

    def test_empty_model_setting_falls_back_to_default(self) -> None:
        client = FakeClient(SAMPLE_RESULT.model_dump_json())

        with patch.dict(os.environ, {"DEEPSEEK_MODEL": "   "}):
            analyze_jd("一段 JD", client=client)

        self.assertEqual(client.chat.completions.last_request["model"], DEFAULT_MODEL)

    def test_rejects_empty_jd_before_api_call(self) -> None:
        client = FakeClient(SAMPLE_RESULT.model_dump_json())

        with self.assertRaisesRegex(ValueError, "不能为空"):
            analyze_jd("   ", client=client)

        self.assertIsNone(client.chat.completions.last_request)

    def test_reports_missing_output(self) -> None:
        client = FakeClient(None)

        with self.assertRaisesRegex(RuntimeError, "没有返回"):
            analyze_jd("一段 JD", client=client)

    def test_rejects_json_with_missing_field(self) -> None:
        client = FakeClient('{"job_title": "内容运营专员"}')

        with self.assertRaises(ValueError):
            analyze_jd("一段 JD", client=client)


if __name__ == "__main__":
    unittest.main()
