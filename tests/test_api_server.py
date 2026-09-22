"""Offline checks for the Vue bridge's consent, privacy, and request limits."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api_server
from models import JobGroupProfile, ResumeFeedback


JOBS = [
    {
        "id": "manual:one",
        "source": "手动添加",
        "title": "内容运营 A",
        "company": "甲公司",
        "location": "武汉",
        "jd_text": "负责文案写作和数据整理。",
    },
    {
        "id": "manual:two",
        "source": "手动添加",
        "title": "内容运营 B",
        "company": "乙公司",
        "location": "武汉",
        "jd_text": "负责数据整理与活动策划。",
    },
]


def sample_profile():
    return JobGroupProfile.model_validate(
        {
            "direction_name": "内容运营",
            "summary": "两条岗位都提到了数据整理。",
            "consistency_summary": "两份样本方向相近。",
            "job_ids": ["manual:one", "manual:two"],
            "outlier_job_ids": [],
            "signals": [
                {
                    "label": "数据整理",
                    "category": "专业能力",
                    "evidence": [
                        {"job_id": "manual:one", "quote": "数据整理"},
                        {"job_id": "manual:two", "quote": "数据整理"},
                    ],
                }
            ],
        }
    )


class ApiServerTests(unittest.TestCase):
    def test_search_uses_job_source_without_spending_model_request(self):
        with patch.object(api_server, "get_public_test_key", return_value="test-key"), patch.object(
            api_server,
            "search_jobs",
            side_effect=lambda keyword, **kwargs: {
                "items": JOBS,
                "total": 2,
                "offset": kwargs["offset"],
                "limit": 20,
            },
        ), TestClient(api_server.app) as client:
            self.assertEqual(client.get("/api/jobs/search", params={"q": "运营"}).json()["total"], 2)
            self.assertEqual(client.get("/api/meta").json()["used_model_requests"], 0)

    def test_group_analysis_requires_explicit_consent(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}), patch.object(
            api_server, "analyze_job_group", side_effect=AssertionError("must not call")
        ), TestClient(api_server.app) as client:
            response = client.post("/api/analysis/group", json={"jobs": JOBS, "consent": False})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(client.get("/api/meta").json()["used_model_requests"], 0)

    def test_group_profile_and_report_reuse_existing_python_logic(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}), patch.object(
            api_server, "analyze_job_group", return_value=sample_profile()
        ), TestClient(api_server.app) as client:
            result = client.post("/api/analysis/group", json={"jobs": JOBS, "consent": True})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["profile"]["signals"][0]["label"], "数据整理")
            self.assertEqual(client.get("/api/meta").json()["used_model_requests"], 1)
            report = client.post("/api/reports/profile", json={"jobs": JOBS, "profile": result.json()["profile"]})
            self.assertEqual(report.status_code, 200)
            self.assertIn("数据整理", report.json()["text"])

    def test_single_resume_redacts_contacts_before_model(self):
        seen = {}

        def fake_match(jd_text, resume_text):
            seen["resume"] = resume_text
            return ResumeFeedback(
                summary="可以补充例子。", matched_points=[], gaps=[], resume_edits=[], learning_priorities=[]
            )

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}), patch.object(
            api_server, "match_resume", side_effect=fake_match
        ), TestClient(api_server.app) as client:
            response = client.post(
                "/api/analysis/single",
                json={"job": JOBS[0], "resume_text": "我的邮箱是 test@example.com，我做过内容运营。", "consent": True},
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("test@example.com", seen["resume"])
            self.assertIn("[邮箱已隐藏]", seen["resume"])

    def test_group_resume_rejects_untraceable_profile_without_spending(self):
        profile = sample_profile().model_dump()
        profile["signals"][0]["evidence"][0]["quote"] = "原文里没有的要求"
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}), TestClient(api_server.app) as client:
            response = client.post(
                "/api/analysis/group-resume",
                json={"jobs": JOBS, "profile": profile, "resume_text": "我做过内容运营。", "consent": True},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(client.get("/api/meta").json()["used_model_requests"], 0)


if __name__ == "__main__":
    unittest.main()
