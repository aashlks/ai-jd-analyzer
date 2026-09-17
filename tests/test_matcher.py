"""Offline tests for evidence-based resume feedback."""

import json
import unittest
from types import SimpleNamespace

from matcher import FeedbackFormatError, match_resume
from models import ResumeFeedback


JD = "要求熟悉 Python；有 RAG 项目经验者优先。"
RESUME = "使用 Python 完成数据处理项目。"

SAMPLE_FEEDBACK = ResumeFeedback(
    summary="简历展示了 Python 经历，RAG 项目尚未体现。",
    matched_points=[
        {
            "requirement": "Python",
            "jd_quote": "熟悉 Python",
            "resume_quote": "使用 Python 完成数据处理项目",
        }
    ],
    gaps=[
        {
            "requirement": "RAG 项目",
            "jd_quote": "有 RAG 项目经验者优先",
            "explanation": "简历未体现相关项目",
        }
    ],
    resume_edits=["写清数据处理项目中自己负责的部分"],
    learning_priorities=["如确实感兴趣，可做一个小型 RAG 项目"],
)


class FakeClient:
    def __init__(self, content: str | None, finish_reason: str = "stop") -> None:
        self.last_request = None
        self.content = content
        self.finish_reason = finish_reason
        self.calls = 0
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.calls += 1
        self.last_request = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content),
                    finish_reason=self.finish_reason,
                )
            ]
        )


class MatcherTests(unittest.TestCase):
    def test_accepts_verifiable_quotes_and_sends_both_inputs(self) -> None:
        client = FakeClient(SAMPLE_FEEDBACK.model_dump_json())

        feedback = match_resume(JD, RESUME, client=client, model="test-model")

        self.assertEqual(feedback.matched_points[0].requirement, "Python")
        self.assertEqual(client.last_request["model"], "test-model")
        self.assertEqual(
            client.last_request["extra_body"], {"thinking": {"type": "disabled"}}
        )
        self.assertEqual(client.last_request["max_tokens"], 4000)
        self.assertIn(JD, client.last_request["messages"][1]["content"])
        self.assertIn(RESUME, client.last_request["messages"][1]["content"])

    def test_accepts_nontechnical_job_feedback(self) -> None:
        jd = "内容运营专员：负责活动策划，要求具备文案写作能力。"
        resume = "曾独立策划校园活动，并负责公众号文案写作。"
        feedback = ResumeFeedback(
            summary="简历有活动策划和文案经历。",
            matched_points=[
                {
                    "requirement": "文案写作",
                    "jd_quote": "具备文案写作能力",
                    "resume_quote": "负责公众号文案写作",
                }
            ],
            gaps=[],
            resume_edits=["可在已有活动经历中写清个人职责"],
            learning_priorities=[],
        )
        client = FakeClient(feedback.model_dump_json())

        result = match_resume(jd, resume, client=client)

        self.assertEqual(result.matched_points[0].requirement, "文案写作")
        self.assertIn("不预设任何技能类别", client.last_request["messages"][0]["content"])

    def test_rejects_invented_resume_quote(self) -> None:
        payload = SAMPLE_FEEDBACK.model_dump()
        payload["matched_points"][0]["resume_quote"] = "我开发了十个 AI 产品"
        client = FakeClient(ResumeFeedback.model_validate(payload).model_dump_json())

        with self.assertRaisesRegex(ValueError, "证据"):
            match_resume(JD, RESUME, client=client)

    def test_accepts_safe_json_variations_without_second_api_call(self) -> None:
        payload = SAMPLE_FEEDBACK.model_dump()
        payload["matched_points"] = {
            **payload["matched_points"][0], "confidence": 0.9
        }
        payload["resume_edits"] = "写清自己负责的部分"
        del payload["learning_priorities"]
        payload["match_score"] = 90
        client = FakeClient(json.dumps(payload, ensure_ascii=False))

        result = match_resume(JD, RESUME, client=client)

        self.assertEqual(len(result.matched_points), 1)
        self.assertEqual(result.resume_edits, ["写清自己负责的部分"])
        self.assertEqual(result.learning_priorities, [])
        self.assertFalse(hasattr(result, "match_score"))

    def test_reports_invalid_field_without_exposing_response_text(self) -> None:
        payload = SAMPLE_FEEDBACK.model_dump()
        payload["matched_points"][0]["resume_quote"] = None
        client = FakeClient(json.dumps(payload, ensure_ascii=False))

        with self.assertRaises(FeedbackFormatError) as caught:
            match_resume(JD, RESUME, client=client)

        self.assertIn("matched_points.0.resume_quote", str(caught.exception))
        self.assertNotIn(RESUME, str(caught.exception))

    def test_reports_incomplete_json_without_exposing_response_text(self) -> None:
        client = FakeClient('{"summary": "包含私人文字"')

        with self.assertRaisesRegex(FeedbackFormatError, "不是完整的 JSON") as caught:
            match_resume(JD, RESUME, client=client)

        self.assertNotIn("私人文字", str(caught.exception))

    def test_reports_length_truncation_without_retrying(self) -> None:
        client = FakeClient('{"summary": "未写完"', finish_reason="length")

        with self.assertRaisesRegex(FeedbackFormatError, "长度上限"):
            match_resume(JD, RESUME, client=client)

        self.assertEqual(client.calls, 1)

    def test_rejects_missing_input(self) -> None:
        client = FakeClient(SAMPLE_FEEDBACK.model_dump_json())

        with self.assertRaisesRegex(ValueError, "不能为空"):
            match_resume(JD, " ", client=client)

        self.assertIsNone(client.last_request)

    def test_rejects_very_long_resume_before_api_call(self) -> None:
        client = FakeClient(SAMPLE_FEEDBACK.model_dump_json())

        with self.assertRaisesRegex(ValueError, "过长"):
            match_resume(JD, "P" * 16001, client=client)

        self.assertIsNone(client.last_request)


if __name__ == "__main__":
    unittest.main()
