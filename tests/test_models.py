"""Tests for the fixed JSON-shaped result model."""

import unittest

from pydantic import ValidationError

from models import JobAnalysis, JobGroupProfile


VALID_PAYLOAD = {
    "job_title": "内容运营专员",
    "company": "示例公司",
    "employment_type": "正式",
    "location": "武汉",
    "responsibilities": ["策划并发布内容"],
    "required_skills": ["文案写作", "数据复盘"],
    "other_requirements": [],
    "education_requirement": "本科及以上",
    "experience_requirement": "1 年以上相关经验",
    "work_schedule": "未提及",
    "bonus_points": ["有账号运营经验"],
}


class JobAnalysisTests(unittest.TestCase):
    def test_accepts_general_job_fields(self) -> None:
        result = JobAnalysis.model_validate(VALID_PAYLOAD)

        self.assertEqual(len(JobAnalysis.model_fields), 11)
        self.assertEqual(result.required_skills, ["文案写作", "数据复盘"])

    def test_rejects_missing_field(self) -> None:
        invalid_payload = VALID_PAYLOAD.copy()
        del invalid_payload["company"]

        with self.assertRaises(ValidationError):
            JobAnalysis.model_validate(invalid_payload)

    def test_rejects_unknown_field(self) -> None:
        invalid_payload = {**VALID_PAYLOAD, "salary": "面议"}

        with self.assertRaises(ValidationError):
            JobAnalysis.model_validate(invalid_payload)

    def test_group_profile_accepts_all_industry_categories(self) -> None:
        profile = JobGroupProfile.model_validate(
            {
                "direction_name": "财务助理",
                "summary": "样本关注凭证整理和表格工具。",
                "consistency_summary": "岗位方向一致。",
                "job_ids": ["finance-1", "finance-2"],
                "outlier_job_ids": [],
                "signals": [
                    {
                        "label": "凭证整理",
                        "category": "专业能力",
                        "evidence": [{"job_id": "finance-1", "quote": "整理财务凭证"}],
                    }
                ],
            }
        )

        self.assertEqual(profile.signals[0].category, "专业能力")


if __name__ == "__main__":
    unittest.main()
