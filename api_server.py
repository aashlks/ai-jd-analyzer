"""Small HTTP bridge for the Ant Design Vue frontend.

The LLM and job-source credentials stay in Python; the browser only sees the
jobs and analysis results it asked for. The original Streamlit app remains
available while the new frontend is tested locally.
"""

import os
import secrets
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAIError, RateLimitError
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from group_analyzer import GroupAnalysisFormatError, analyze_job_group, match_resume_to_group
from job_sources import JobSourceError, get_public_test_key, search_jobs
from matcher import FeedbackFormatError, match_resume
from models import GroupResumeFeedback, JobGroupProfile, ResumeFeedback
from report_export import (
    build_group_profile_report,
    build_group_resume_report,
    build_single_resume_report,
    report_filename,
)
from resume_reader import MAX_FILE_BYTES, ResumeReadError, extract_resume_text, redact_basic_contacts

load_dotenv()
app = FastAPI(title="求职对照台 API")


def positive_env_int(name: str, default: int) -> int:
    try:
        number = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return number if number > 0 else default


MAX_REQUESTS = positive_env_int("MAX_MODEL_REQUESTS_PER_SESSION", 8)
SESSION_TTL = 60 * 60
_usage: dict[str, tuple[int, float]] = {}
_usage_lock = threading.Lock()


class JobRecord(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    source: str = Field(default="手动添加", max_length=40)
    title: str = Field(default="未填写", max_length=200)
    company: str = Field(default="未填写", max_length=200)
    location: str = Field(default="未提及", max_length=200)
    jd_text: str = Field(min_length=1, max_length=20000)
    url: str = Field(default="", max_length=2000)
    original_url: str = Field(default="", max_length=2000)
    published_at: str = Field(default="", max_length=100)


class GroupRequest(BaseModel):
    jobs: list[JobRecord] = Field(min_length=2, max_length=10)
    consent: bool


class GroupResumeRequest(BaseModel):
    jobs: list[JobRecord] = Field(min_length=2, max_length=10)
    profile: JobGroupProfile
    resume_text: str = Field(min_length=1, max_length=16000)
    consent: bool


class SingleResumeRequest(BaseModel):
    job: JobRecord
    resume_text: str = Field(min_length=1, max_length=16000)
    consent: bool


class ProfileReportRequest(BaseModel):
    jobs: list[JobRecord]
    profile: JobGroupProfile


class GroupReportRequest(ProfileReportRequest):
    feedback: GroupResumeFeedback


class SingleReportRequest(BaseModel):
    job: JobRecord
    feedback: ResumeFeedback


@app.middleware("http")
async def assign_browser_session(request: Request, call_next):
    token = request.cookies.get("jd_browser_session", "")
    if len(token) != 32 or any(char not in "0123456789abcdef" for char in token):
        token = secrets.token_hex(16)
        new_session = True
    else:
        new_session = False
    request.state.session_token = token
    response = await call_next(request)
    if new_session:
        response.set_cookie(
            "jd_browser_session",
            token,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
    return response


def _usage_count(token: str) -> int:
    now = time.monotonic()
    with _usage_lock:
        for key, (_, updated) in list(_usage.items()):
            if now - updated > SESSION_TTL:
                del _usage[key]
        count, _ = _usage.get(token, (0, now))
        _usage[token] = (count, now)
        return count


def _reserve_model_request(request: Request, consent: bool) -> None:
    if not consent:
        raise HTTPException(status_code=400, detail="请先确认本次模型请求和可能产生的费用。")
    if not os.getenv("DEEPSEEK_API_KEY", "").strip():
        raise HTTPException(status_code=503, detail="服务端尚未配置 DeepSeek Key，暂时不能生成分析。")
    token = request.state.session_token
    now = time.monotonic()
    with _usage_lock:
        count, updated = _usage.get(token, (0, now))
        if now - updated > SESSION_TTL:
            count = 0
        if count >= MAX_REQUESTS:
            raise HTTPException(status_code=429, detail="当前浏览会话的模型请求次数已用完。")
        _usage[token] = (count + 1, now)


def _safe_error(error: Exception) -> HTTPException:
    if isinstance(error, AuthenticationError):
        return HTTPException(status_code=502, detail="DeepSeek Key 无效，请检查服务端配置。")
    if isinstance(error, RateLimitError):
        return HTTPException(status_code=429, detail="DeepSeek 当前限流或余额不足，请稍后检查平台额度。")
    if isinstance(error, APIConnectionError):
        return HTTPException(status_code=502, detail="暂时无法连接 DeepSeek，请检查网络。")
    if isinstance(error, APIStatusError):
        return HTTPException(status_code=502, detail="DeepSeek 暂时没有返回可用结果，请稍后再试。")
    if isinstance(error, (GroupAnalysisFormatError, FeedbackFormatError)):
        return HTTPException(status_code=502, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=400, detail=str(error))
    if isinstance(error, OpenAIError):
        return HTTPException(status_code=502, detail="模型请求失败，请稍后再试。")
    return HTTPException(status_code=500, detail="服务器暂时无法完成分析；没有自动重试模型请求。")


def _job_dicts(jobs: list[JobRecord]) -> list[dict]:
    return [job.model_dump() for job in jobs]


def _check_profile_matches_jobs(profile: JobGroupProfile, jobs: list[JobRecord]) -> None:
    job_map = {job.id: job.jd_text for job in jobs}
    if len(job_map) != len(jobs) or set(profile.job_ids) != set(job_map):
        raise HTTPException(status_code=400, detail="岗位样本与画像不一致，请重新生成画像。")
    for signal in profile.signals:
        for evidence in signal.evidence:
            source = job_map.get(evidence.job_id, "")
            compact_quote = "".join(evidence.quote.split()).casefold()
            compact_source = "".join(source.split()).casefold()
            if not compact_quote or compact_quote not in compact_source:
                raise HTTPException(status_code=400, detail="画像证据与岗位原文不一致，请重新生成画像。")


@app.get("/api/meta")
def meta(request: Request):
    used = _usage_count(request.state.session_token)
    return {"max_model_requests": MAX_REQUESTS, "used_model_requests": used}


@app.get("/api/jobs/search")
async def find_jobs(
    q: str = Query(min_length=1, max_length=50),
    city: str = Query(default="", max_length=50),
    employment_type: str = Query(default="", pattern="^(|实习|正式)$"),
    offset: int = Query(default=0, ge=0),
):
    try:
        key = os.getenv("OFFERDAO_API_KEY", "").strip() or await run_in_threadpool(get_public_test_key)
        return await run_in_threadpool(
            search_jobs, q, city=city, employment_type=employment_type,
            api_key=key, limit=20, offset=offset,
        )
    except JobSourceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/resume/extract")
async def extract_resume(file: UploadFile = File(...)):
    try:
        content = await file.read(MAX_FILE_BYTES + 1)
        text = await run_in_threadpool(extract_resume_text, file.filename or "", content)
        return {"text": redact_basic_contacts(text)}
    except ResumeReadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await file.close()


@app.post("/api/analysis/group")
async def group_analysis(body: GroupRequest, request: Request):
    _reserve_model_request(request, body.consent)
    try:
        profile = await run_in_threadpool(analyze_job_group, _job_dicts(body.jobs))
        return {"profile": profile.model_dump(), "used_model_requests": _usage_count(request.state.session_token)}
    except Exception as error:
        raise _safe_error(error) from error


@app.post("/api/analysis/group-resume")
async def group_resume_analysis(body: GroupResumeRequest, request: Request):
    _check_profile_matches_jobs(body.profile, body.jobs)
    _reserve_model_request(request, body.consent)
    try:
        feedback = await run_in_threadpool(
            match_resume_to_group, body.profile, redact_basic_contacts(body.resume_text)
        )
        return {"feedback": feedback.model_dump(), "used_model_requests": _usage_count(request.state.session_token)}
    except Exception as error:
        raise _safe_error(error) from error


@app.post("/api/analysis/single")
async def single_analysis(body: SingleResumeRequest, request: Request):
    _reserve_model_request(request, body.consent)
    try:
        feedback = await run_in_threadpool(
            match_resume, body.job.jd_text, redact_basic_contacts(body.resume_text)
        )
        return {"feedback": feedback.model_dump(), "used_model_requests": _usage_count(request.state.session_token)}
    except Exception as error:
        raise _safe_error(error) from error


@app.post("/api/reports/profile")
def profile_report(body: ProfileReportRequest):
    _check_profile_matches_jobs(body.profile, body.jobs)
    return {
        "filename": report_filename(body.profile.direction_name, "岗位方向画像"),
        "text": build_group_profile_report(body.profile, _job_dicts(body.jobs)),
    }


@app.post("/api/reports/group-resume")
def group_resume_report(body: GroupReportRequest):
    _check_profile_matches_jobs(body.profile, body.jobs)
    return {
        "filename": report_filename(body.profile.direction_name, "简历对照建议"),
        "text": build_group_resume_report(body.feedback, body.profile),
    }


@app.post("/api/reports/single")
def single_report(body: SingleReportRequest):
    return {
        "filename": report_filename(body.job.title, "单岗位简历建议"),
        "text": build_single_resume_report(body.feedback, body.job.model_dump()),
    }


# In production, build frontend/ first; Vite serves it directly during local development.
DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="找不到这个 API 地址。")
    if path == "favicon.svg":
        return FileResponse(DIST / "favicon.svg")
    index = DIST / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="请先运行前端开发服务器，或构建 frontend。")
    return FileResponse(index)
