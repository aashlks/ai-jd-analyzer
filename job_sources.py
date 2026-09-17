"""Fetch a small set of jobs through OfferDAO's documented API."""

import os
from urllib.parse import quote, urlparse

import httpx


DEFAULT_BASE_URL = "https://offerdao.ai"
REQUEST_TIMEOUT = 15.0

class JobSourceError(Exception):
    """A readable error while loading jobs from an external source."""


def _base_url() -> str:
    return (os.getenv("OFFERDAO_BASE") or DEFAULT_BASE_URL).rstrip("/")


def _read_json(response: httpx.Response) -> dict:
    if response.status_code == 429:
        raise JobSourceError("岗位来源的查询额度暂时用完了，请稍后再试。")
    if response.status_code == 401:
        raise JobSourceError("岗位来源的 API Key 无效，请检查 OFFERDAO_API_KEY。")

    try:
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPStatusError, ValueError) as error:
        raise JobSourceError("岗位来源暂时没有返回可用数据，请稍后再试。") from error

    if not isinstance(data, dict):
        raise JobSourceError("岗位来源返回了意外的数据格式。")
    return data


def get_public_test_key() -> str:
    """Get OfferDAO's shared, read-only test key for a local prototype."""

    try:
        response = httpx.get(
            f"{_base_url()}/api/v1/agent/test-key", timeout=REQUEST_TIMEOUT
        )
    except httpx.RequestError as error:
        raise JobSourceError("无法连接岗位来源，请检查网络。") from error

    key = _read_json(response).get("key")
    if not isinstance(key, str) or not key.strip():
        raise JobSourceError("岗位来源没有返回测试 Key。")
    return key.strip()


def search_jobs(
    keyword: str,
    *,
    city: str = "",
    employment_type: str = "",
    api_key: str,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """Search jobs without assuming an industry or employment type."""

    keyword = keyword.strip()
    city = city.strip()
    employment_type = employment_type.strip()
    if not keyword:
        raise ValueError("请填写岗位关键词。")
    if not api_key.strip():
        raise ValueError("岗位来源的 API Key 不能为空。")
    if not 1 <= limit <= 20:
        raise ValueError("一次最多查询 20 个岗位。")
    if offset < 0:
        raise ValueError("岗位结果的起始位置不能为负数。")
    if employment_type not in ("", "实习", "正式"):
        raise ValueError("目前只支持不限、实习或正式的用工类型筛选。")

    base_url = _base_url()
    params = {"q": keyword, "limit": limit, "offset": offset}
    if city:
        params["location"] = city
    if employment_type:
        params["employment_type"] = employment_type

    try:
        response = httpx.get(
            f"{base_url}/api/v1/postings/search",
            params=params,
            headers={"Authorization": f"Bearer {api_key.strip()}"},
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.RequestError as error:
        raise JobSourceError("无法连接岗位来源，请检查网络。") from error

    data = _read_json(response)
    items = data.get("items")
    if not isinstance(items, list):
        raise JobSourceError("岗位来源返回的职位列表格式不正确。")

    jobs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        posting_id = str(item.get("posting_id") or "").strip()
        title = str(item.get("role") or "").strip()
        if not posting_id or not title:
            continue

        company = str(item.get("organization") or "未提及").strip()
        location = str(item.get("location") or "未提及").strip()
        parts = [f"岗位名称：{title}", f"公司：{company}", f"地点：{location}"]
        for label, field in (
            ("岗位简介", "intro"),
            ("岗位描述", "description"),
            ("任职要求", "requirements"),
        ):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                parts.append(f"{label}：\n{value.strip()}")

        original_url = item.get("source_url")
        parsed_url = urlparse(original_url) if isinstance(original_url, str) else None
        if (
            not parsed_url
            or parsed_url.scheme not in ("http", "https")
            or not parsed_url.netloc
        ):
            original_url = ""

        jobs.append(
            {
                "id": f"offerdao:{posting_id}",
                "source": "Offer岛",
                "title": title,
                "company": company,
                "location": location,
                "jd_text": "\n\n".join(parts),
                "url": f"{base_url}/j/{quote(posting_id, safe='')}",
                "original_url": original_url,
                "published_at": str(item.get("published_at") or ""),
            }
        )

    total = data.get("total")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        total = offset + len(jobs)
    return {"items": jobs, "total": total, "offset": offset, "limit": limit}
