"""Readable report exports must preserve evidence without exposing JSON."""

import unittest

from models import GroupResumeFeedback, JobGroupProfile, ResumeFeedback
from report_export import (
    build_group_profile_report,
    build_group_resume_report,
    build_single_resume_report,
    report_filename,
)


JOBS = [
    {
        "id": "job-1",
        "title": "内容运营实习生",
        "company": "甲公司",
        "source": "手动添加",
    },
    {
        "id": "job-2",
        "title": "新媒体运营实习生",
        "company": "乙公司",
        "source": "Offer岛",
    },
]

PROFILE = JobGroupProfile.model_validate(
    {
        "direction_name": "内容运营",
        "summary": "样本关注内容策划与复盘。",
        "consistency_summary": "方向大体一致。",
        "job_ids": ["job-1", "job-2"],
        "outlier_job_ids": [],
        "signals": [
            {
                "label": "内容策划",
                "category": "岗位职责",
                "evidence": [
                    {"job_id": "job-1", "quote": "负责内容策划"},
                    {"job_id": "job-2", "quote": "完成选题策划"},
                ],
            }
        ],
    }
)


class ReportExportTests(unittest.TestCase):
    def test_group_profile_report_is_readable_and_evidence_backed(self) -> None:
        report = build_group_profile_report(PROFILE, JOBS)

        self.assertIn("岗位方向画像", report)
        self.assertIn("内容策划（岗位职责，2/2 个岗位提到）", report)
        self.assertIn("负责内容策划", report)
        self.assertNotIn('"signals"', report)

    def test_group_resume_report_keeps_frequency_and_resume_quote(self) -> None:
        feedback = GroupResumeFeedback.model_validate(
            {
                "summary": "已有部分内容经验。",
                "matched_capabilities": [
                    {
                        "requirement": "内容策划",
                        "resume_quote": "负责校园公众号选题",
                        "explanation": "能支持内容策划能力。",
                    }
                ],
                "gaps": [],
                "resume_edits": ["补充真实内容数据。"],
                "action_plan": ["整理现有作品。"],
            }
        )

        report = build_group_resume_report(feedback, PROFILE)

        self.assertIn("2/2 个岗位提到", report)
        self.assertIn("负责校园公众号选题", report)
        self.assertIn("整理现有作品", report)

    def test_single_report_and_filename_are_portable(self) -> None:
        feedback = ResumeFeedback.model_validate(
            {
                "summary": "简历已有相关经历。",
                "matched_points": [
                    {
                        "requirement": "文案能力",
                        "jd_quote": "具备文案能力",
                        "resume_quote": "撰写十篇推文",
                    }
                ],
                "gaps": [],
                "resume_edits": [],
                "learning_priorities": [],
            }
        )

        report = build_single_resume_report(feedback, JOBS[0])

        self.assertIn("单岗位简历精读", report)
        self.assertIn("撰写十篇推文", report)
        self.assertEqual(report_filename('内容/运营:*?<>|', "建议"), "内容_运营-建议.txt")


if __name__ == "__main__":
    unittest.main()
