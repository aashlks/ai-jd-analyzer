"""Offline tests for the automatic job source; no live API calls."""

import unittest
from unittest.mock import patch

import httpx

from job_sources import (
    JobSourceError,
    get_public_test_key,
    search_jobs,
)


class JobSourceTests(unittest.TestCase):
    @patch("job_sources.httpx.get")
    def test_reads_public_test_key(self, get) -> None:
        get.return_value = httpx.Response(
            200,
            json={"key": "test-only-key"},
            request=httpx.Request("GET", "https://offerdao.ai/api/v1/agent/test-key"),
        )

        self.assertEqual(get_public_test_key(), "test-only-key")

    @patch("job_sources.httpx.get")
    def test_searches_nontechnical_job_without_employment_filter(self, get) -> None:
        get.return_value = httpx.Response(
            200,
            json={
                "total": 1,
                "items": [
                    {
                        "posting_id": "job-123",
                        "role": "内容运营专员",
                        "organization": "示例公司",
                        "location": "武汉",
                        "description": "策划并发布内容",
                        "requirements": "具备文案写作能力",
                        "source_url": "https://example.com/job-123",
                        "published_at": "2026-09-12",
                    }
                ],
            },
            request=httpx.Request("GET", "https://offerdao.ai/api/v1/postings/search"),
        )

        result = search_jobs("内容运营", city="武汉", api_key="test-only-key")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "offerdao:job-123")
        self.assertIn("具备文案写作能力", result["items"][0]["jd_text"])
        self.assertEqual(result["items"][0]["original_url"], "https://example.com/job-123")
        request_kwargs = get.call_args.kwargs
        self.assertNotIn("employment_type", request_kwargs["params"])
        self.assertEqual(request_kwargs["params"]["location"], "武汉")
        self.assertEqual(request_kwargs["params"]["q"], "内容运营")
        self.assertEqual(request_kwargs["params"]["offset"], 0)
        self.assertEqual(request_kwargs["headers"]["Authorization"], "Bearer test-only-key")

    @patch("job_sources.httpx.get")
    def test_filters_internships_only_when_requested(self, get) -> None:
        get.return_value = httpx.Response(
            200,
            json={"total": 0, "items": []},
            request=httpx.Request("GET", "https://offerdao.ai/api/v1/postings/search"),
        )

        search_jobs("运营", employment_type="实习", api_key="test-only-key")

        self.assertEqual(get.call_args.kwargs["params"]["employment_type"], "实习")

    @patch("job_sources.httpx.get")
    def test_reports_shared_key_limit(self, get) -> None:
        get.return_value = httpx.Response(
            429,
            request=httpx.Request("GET", "https://offerdao.ai/api/v1/postings/search"),
        )

        with self.assertRaisesRegex(JobSourceError, "额度"):
            search_jobs("AI", api_key="test-only-key")

    def test_rejects_empty_keyword_before_request(self) -> None:
        with self.assertRaisesRegex(ValueError, "关键词"):
            search_jobs("  ", api_key="test-only-key")

    @patch("job_sources.httpx.get")
    def test_search_uses_offset_for_next_page(self, get) -> None:
        get.return_value = httpx.Response(
            200,
            json={"total": 37, "items": []},
            request=httpx.Request("GET", "https://offerdao.ai/api/v1/postings/search"),
        )

        result = search_jobs("运营", api_key="test-only-key", limit=20, offset=20)

        self.assertEqual(get.call_args.kwargs["params"], {"q": "运营", "limit": 20, "offset": 20})
        self.assertEqual(result["offset"], 20)
        self.assertEqual(result["total"], 37)

    def test_rejects_negative_offset(self) -> None:
        with self.assertRaisesRegex(ValueError, "起始位置"):
            search_jobs("运营", api_key="test-only-key", offset=-1)


if __name__ == "__main__":
    unittest.main()
