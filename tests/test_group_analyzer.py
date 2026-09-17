"""Offline tests for multi-JD profiles and group-level resume advice."""

import json
import unittest
from types import SimpleNamespace

from group_analyzer import (
    GroupAnalysisFormatError,
    analyze_job_group,
    match_resume_to_group,
)
from models import JobGroupProfile, GroupResumeFeedback


JOBS = [
    {
        "id": "job-1",
        "title": "内容运营实习生",
        "company": "甲公司",
        "jd_text": "负责公众号内容策划与撰写，定期进行数据复盘。",
    },
    {
        "id": "job-2",
        "title": "新媒体运营实习生",
        "company": "乙公司",
        "jd_text": "完成短视频选题与文案，使用 Excel 整理运营数据。",
    },
]


PROFILE_PAYLOAD = {
    "direction_name": "内容运营实习",
    "summary": "这些样本主要关注内容生产与数据整理。",
    "consistency_summary": "两条岗位都属于内容运营方向。",
    "outlier_job_ids": [],
    "signals": [
        {
            "label": "内容策划与文案",
            "category": "岗位职责",
            "evidence": [
                {"job_id": "job-1", "quote": "公众号内容策划与撰写"},
                {"job_id": "job-2", "quote": "短视频选题与文案"},
            ],
        },
        {
            "label": "数据整理与复盘",
            "category": "专业能力",
            "evidence": [
                {"job_id": "job-1", "quote": "数据复盘"},
                {"job_id": "job-2", "quote": "整理运营数据"},
            ],
        },
    ],
}


FEEDBACK_PAYLOAD = {
    "summary": "简历体现了内容策划，但数据复盘证据不足。",
    "matched_capabilities": [
        {
            "requirement": "内容策划与文案",
            "resume_quote": "负责校园公众号选题与文案",
            "explanation": "这段经历直接体现了内容策划。",
        }
    ],
    "gaps": [
        {
            "requirement": "数据整理与复盘",
            "explanation": "简历未清楚说明数据指标和复盘结论。",
        }
    ],
    "resume_edits": ["如经历真实，可补充阅读量和复盘结论。"],
    "action_plan": ["先整理已有内容运营项目的数据结果。"],
}


class FakeClient:
    def __init__(self, content: str | None, finish_reason: str = "stop") -> None:
        self.content = content
        self.finish_reason = finish_reason
        self.calls = 0
        self.last_request = None
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


class GroupAnalyzerTests(unittest.TestCase):
    def test_builds_profile_and_keeps_authoritative_job_ids(self) -> None:
        client = FakeClient(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))

        profile = analyze_job_group(JOBS, client=client, model="test-model")

        self.assertEqual(profile.direction_name, "内容运营实习")
        self.assertEqual(profile.job_ids, ["job-1", "job-2"])
        self.assertEqual(len(profile.signals[0].evidence), 2)
        self.assertEqual(client.calls, 1)
        self.assertEqual(client.last_request["model"], "test-model")
        self.assertEqual(client.last_request["extra_body"], {"thinking": {"type": "disabled"}})
        sent = client.last_request["messages"][1]["content"]
        self.assertIn("job-1", sent)
        self.assertIn(JOBS[1]["jd_text"], sent)

    def test_rejects_unverifiable_jd_quote(self) -> None:
        payload = json.loads(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))
        payload["signals"][0]["evidence"][0]["quote"] = "负责十万粉丝账号"

        with self.assertRaisesRegex(ValueError, "证据"):
            analyze_job_group(JOBS, client=FakeClient(json.dumps(payload, ensure_ascii=False)))

    def test_accepts_harmless_profile_variations_without_second_call(self) -> None:
        payload = json.loads(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))
        payload["confidence"] = 0.9
        payload["signals"] = {**payload["signals"][0], "frequency": 99}
        payload["signals"]["evidence"] = {
            **payload["signals"]["evidence"][0],
            "reason": "模型附带的无关解释",
        }
        client = FakeClient(json.dumps(payload, ensure_ascii=False))

        profile = analyze_job_group(JOBS, client=client)

        self.assertEqual(len(profile.signals), 1)
        self.assertEqual(len(profile.signals[0].evidence), 1)
        self.assertEqual(client.calls, 1)

    def test_merges_repeated_signal_labels_without_double_counting(self) -> None:
        payload = json.loads(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))
        payload["signals"] = [
            {
                "label": "内容策划与文案",
                "category": "岗位职责",
                "evidence": [{"job_id": "job-1", "quote": "公众号内容策划与撰写"}],
            },
            {
                "label": " 内容策划与文案 ",
                "category": "专业能力",
                "evidence": [{"job_id": "job-2", "quote": "短视频选题与文案"}],
            },
        ]

        profile = analyze_job_group(
            JOBS, client=FakeClient(json.dumps(payload, ensure_ascii=False))
        )

        self.assertEqual(len(profile.signals), 1)
        self.assertEqual(profile.signals[0].category, "岗位职责")
        self.assertEqual(
            {item.job_id for item in profile.signals[0].evidence}, {"job-1", "job-2"}
        )

    def test_rejects_unknown_or_duplicate_job_evidence(self) -> None:
        payload = json.loads(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))
        payload["signals"][0]["evidence"][0]["job_id"] = "unknown"
        with self.assertRaisesRegex(GroupAnalysisFormatError, "不存在"):
            analyze_job_group(JOBS, client=FakeClient(json.dumps(payload, ensure_ascii=False)))

        payload = json.loads(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))
        payload["signals"][0]["evidence"][1]["job_id"] = "job-1"
        payload["signals"][0]["evidence"][1]["quote"] = "数据复盘"
        with self.assertRaisesRegex(GroupAnalysisFormatError, "重复"):
            analyze_job_group(JOBS, client=FakeClient(json.dumps(payload, ensure_ascii=False)))

    def test_rejects_too_few_or_too_many_jobs_before_api_call(self) -> None:
        client = FakeClient(json.dumps(PROFILE_PAYLOAD, ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, "2 至 10"):
            analyze_job_group(JOBS[:1], client=client)
        with self.assertRaisesRegex(ValueError, "2 至 10"):
            analyze_job_group(JOBS * 6, client=client)
        self.assertEqual(client.calls, 0)

    def test_matches_resume_to_existing_group_signals(self) -> None:
        profile = JobGroupProfile.model_validate({**PROFILE_PAYLOAD, "job_ids": ["job-1", "job-2"]})
        resume = "负责校园公众号选题与文案，并组织两次活动。"
        client = FakeClient(json.dumps(FEEDBACK_PAYLOAD, ensure_ascii=False))

        feedback = match_resume_to_group(profile, resume, client=client)

        self.assertEqual(feedback.matched_capabilities[0].requirement, "内容策划与文案")
        self.assertIn(resume, client.last_request["messages"][1]["content"])
        self.assertIn('"job_count": 2', client.last_request["messages"][1]["content"])

    def test_rejects_invented_resume_quote_or_requirement(self) -> None:
        profile = JobGroupProfile.model_validate({**PROFILE_PAYLOAD, "job_ids": ["job-1", "job-2"]})
        resume = "负责校园公众号选题与文案。"
        payload = json.loads(json.dumps(FEEDBACK_PAYLOAD, ensure_ascii=False))
        payload["matched_capabilities"][0]["resume_quote"] = "管理百万粉丝账号"
        with self.assertRaisesRegex(ValueError, "简历原文"):
            match_resume_to_group(
                profile, resume, client=FakeClient(json.dumps(payload, ensure_ascii=False))
            )

        payload = json.loads(json.dumps(FEEDBACK_PAYLOAD, ensure_ascii=False))
        payload["gaps"][0]["requirement"] = "英语六级"
        with self.assertRaisesRegex(GroupAnalysisFormatError, "不存在"):
            match_resume_to_group(
                profile, resume, client=FakeClient(json.dumps(payload, ensure_ascii=False))
            )

    def test_accepts_harmless_feedback_variations(self) -> None:
        profile = JobGroupProfile.model_validate({**PROFILE_PAYLOAD, "job_ids": ["job-1", "job-2"]})
        resume = "负责校园公众号选题与文案。"
        payload = json.loads(json.dumps(FEEDBACK_PAYLOAD, ensure_ascii=False))
        payload["matched_capabilities"] = {
            **payload["matched_capabilities"][0],
            "score": 88,
        }
        payload["resume_edits"] = "如经历真实，可补充内容数据。"
        payload["match_score"] = 88

        feedback = match_resume_to_group(
            profile, resume, client=FakeClient(json.dumps(payload, ensure_ascii=False))
        )

        self.assertEqual(len(feedback.matched_capabilities), 1)
        self.assertEqual(feedback.resume_edits, ["如经历真实，可补充内容数据。"])
        self.assertFalse(hasattr(feedback, "match_score"))

    def test_reports_truncated_json_without_retry(self) -> None:
        client = FakeClient('{"direction_name": "未完成"', finish_reason="length")
        with self.assertRaisesRegex(GroupAnalysisFormatError, "截断"):
            analyze_job_group(JOBS, client=client)
        self.assertEqual(client.calls, 1)


if __name__ == "__main__":
    unittest.main()
