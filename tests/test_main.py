"""Offline tests for command-line input and JSON output."""

import io
import json
import os
import unittest
from unittest.mock import patch

import main
from models import JobAnalysis


SAMPLE_RESULT = JobAnalysis(
    job_title="内容运营专员",
    company="示例公司",
    employment_type="正式",
    location="武汉",
    responsibilities=["策划并发布内容"],
    required_skills=["文案写作"],
    other_requirements=[],
    education_requirement="本科及以上",
    experience_requirement="1 年以上相关经验",
    work_schedule="未提及",
    bonus_points=["有账号运营经验"],
)


class MainTests(unittest.TestCase):
    def test_read_jd_accepts_multiple_lines_until_end(self) -> None:
        with (
            patch("builtins.input", side_effect=["第一行", "", "第二行", "END"]),
            patch("sys.stderr", new=io.StringIO()),
        ):
            result = main.read_jd()

        self.assertEqual(result, "第一行\n\n第二行")

    def test_missing_api_key_exits_with_clear_error(self) -> None:
        error_output = io.StringIO()

        with (
            patch("main.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch("sys.stderr", new=error_output),
        ):
            exit_code = main.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("DEEPSEEK_API_KEY", error_output.getvalue())

    def test_success_prints_parseable_json(self) -> None:
        standard_output = io.StringIO()

        with (
            patch("main.load_dotenv"),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=True),
            patch("main.read_jd", return_value="一段 JD"),
            patch("main.analyze_jd", return_value=SAMPLE_RESULT),
            patch("sys.stdout", new=standard_output),
            patch("sys.stderr", new=io.StringIO()),
        ):
            exit_code = main.main()

        output_data = json.loads(standard_output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(output_data["job_title"], "内容运营专员")
        self.assertEqual(output_data["required_skills"], ["文案写作"])

    def test_invalid_model_output_has_friendly_error(self) -> None:
        error_output = io.StringIO()

        with (
            patch("main.load_dotenv"),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=True),
            patch("main.read_jd", return_value="一段 JD"),
            patch("main.analyze_jd", side_effect=ValueError("invalid data")),
            patch("sys.stdout", new=io.StringIO()),
            patch("sys.stderr", new=error_output),
        ):
            exit_code = main.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("结构校验", error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
