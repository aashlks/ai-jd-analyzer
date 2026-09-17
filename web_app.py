"""The Streamlit website for collecting and comparing job descriptions."""

import hashlib
import os
from collections import Counter
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)
from pydantic import ValidationError

from group_analyzer import (
    MAX_GROUP_JOBS,
    GroupAnalysisFormatError,
    analyze_job_group,
    match_resume_to_group,
)
from job_sources import JobSourceError, get_public_test_key, search_jobs
from matcher import FeedbackFormatError, match_resume
from models import GroupResumeFeedback, JobGroupProfile, ResumeFeedback
from report_export import (
    build_group_profile_report,
    build_group_resume_report,
    build_single_resume_report,
    report_filename,
)
from resume_reader import ResumeReadError, extract_resume_text, redact_basic_contacts


OFFER_PAGE_SIZE = 20
MAX_MANUAL_JD_CHARS = 20000

# Load local development settings before deriving configurable limits. On
# Streamlit Community Cloud, root-level Secrets are exposed as environment
# variables, so the same code works without committing a secret file.
load_dotenv()


def positive_env_int(name: str, default: int) -> int:
    """Keep deployment limits configurable without breaking on a bad value."""

    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


MAX_MODEL_REQUESTS_PER_SESSION = positive_env_int("MAX_MODEL_REQUESTS_PER_SESSION", 8)
st.set_page_config(page_title="求职对照台", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #223247;
        --muted: #68798c;
        --blue: #6f8fac;
        --blue-dark: #536f89;
        --blue-pale: #eaf1f7;
        --line: #dbe5ed;
        --paper: #ffffff;
        --canvas: #f5f8fb;
    }
    .stApp {
        background:
            radial-gradient(circle at 92% 4%, rgba(157, 183, 205, .18), transparent 26rem),
            var(--canvas);
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: rgba(245, 248, 251, .82); }
    #MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
    .block-container { max-width: 1180px; padding-top: 1.7rem; padding-bottom: 3rem; }
    h1, h2, h3, h4 { color: var(--ink); letter-spacing: -0.02em; }
    p, label { color: var(--ink); }
    [data-testid="stCaptionContainer"] p { color: var(--muted); }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, .88);
        border-color: var(--line);
        border-radius: 16px;
        box-shadow: 0 8px 30px rgba(62, 86, 110, .045);
    }
    .stButton > button, .stLinkButton > a {
        border-radius: 10px;
        border-color: #cddae5;
        min-height: 2.65rem;
        transition: all .16s ease;
    }
    .stButton > button:hover, .stLinkButton > a:hover {
        border-color: var(--blue);
        color: var(--blue-dark);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: var(--blue-dark);
        border-color: var(--blue-dark);
        color: white;
    }
    .stButton > button:disabled {
        background: #edf2f6 !important;
        border-color: #dce5ec !important;
        color: #8b99a7 !important;
        opacity: 1;
        transform: none;
    }
    [data-baseweb="tab-list"] { gap: .55rem; }
    [data-baseweb="tab"] {
        border-radius: 9px 9px 0 0;
        padding-left: 1.1rem;
        padding-right: 1.1rem;
    }
    [data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
    [data-baseweb="select"] > div {
        background: var(--paper);
        border-color: var(--line);
    }
    [data-testid="stMetric"] {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1rem 1.1rem;
    }
    .brand-mark {
        display: flex;
        align-items: center;
        gap: .7rem;
        min-height: 2.75rem;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--ink);
        letter-spacing: .01em;
    }
    .brand-dot {
        width: 1.8rem;
        height: 1.8rem;
        border: 1px solid #91a9bd;
        border-radius: 50%;
        position: relative;
        display: inline-block;
    }
    .brand-dot:after {
        content: "";
        position: absolute;
        width: .55rem;
        height: .55rem;
        background: #7898b3;
        border-radius: 50%;
        top: .57rem;
        left: .57rem;
    }
    .hero {
        padding: 4.6rem 4.2rem;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(255,255,255,.97), rgba(232,240,247,.82));
        box-shadow: 0 22px 65px rgba(64, 91, 117, .08);
        margin: 1.25rem 0 1.4rem;
    }
    .hero-eyebrow {
        color: var(--blue-dark);
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .16em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .hero h1 {
        max-width: 760px;
        font-size: clamp(2.45rem, 5vw, 4.65rem);
        line-height: 1.08;
        margin: 0 0 1.25rem;
    }
    .hero p {
        max-width: 680px;
        color: var(--muted);
        font-size: 1.08rem;
        line-height: 1.8;
        margin: 0;
    }
    .section-kicker {
        color: var(--blue-dark);
        font-size: .8rem;
        font-weight: 700;
        letter-spacing: .12em;
        margin-top: 2.6rem;
        text-transform: uppercase;
    }
    .st-key-mobile-header { display: none; }
    @media (max-width: 700px) {
        .block-container { padding: 1rem 1rem 2.5rem; }
        .hero { padding: 2.6rem 1.5rem; }
        .hero h1 { font-size: 2.35rem; }
        .st-key-desktop-header { display: none; }
        .st-key-mobile-header { display: block; }
        .st-key-mobile-header [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: .45rem !important;
        }
        .st-key-mobile-header [data-testid="stColumn"] {
            min-width: 0 !important;
            width: auto !important;
        }
        .st-key-mobile-header [data-testid="stColumn"]:first-child {
            flex: 1 1 0 !important;
        }
        .st-key-mobile-header [data-testid="stColumn"]:last-child {
            flex: 0 0 5.5rem !important;
            width: 5.5rem !important;
        }
        .st-key-mobile-header [data-testid="stPopoverButton"] {
            min-height: 2.35rem;
            min-width: 0;
            width: 100% !important;
            padding-left: .7rem;
            padding-right: .7rem;
            font-size: .82rem;
            white-space: nowrap;
        }
        .brand-mark { font-size: .95rem; white-space: nowrap; }
        .brand-dot { width: 1.55rem; height: 1.55rem; }
        .brand-dot:after { top: .45rem; left: .45rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# These dictionaries only live in this Streamlit browser session, not a database.
if "saved_jobs" not in st.session_state:
    st.session_state.saved_jobs = {}
if "feedback" not in st.session_state:
    st.session_state.feedback = {}
if "group_profiles" not in st.session_state:
    st.session_state.group_profiles = {}
if "group_feedback" not in st.session_state:
    st.session_state.group_feedback = {}
if "active_page" not in st.session_state:
    st.session_state.active_page = "首页"
elif st.session_state.active_page == "简历分析":
    # Preserve an older browser session after the page was renamed.
    st.session_state.active_page = "分析中心"
    st.session_state.analysis_mode = "单岗位精读"
if "chosen_job_ids" not in st.session_state:
    st.session_state.chosen_job_ids = []
if "model_request_count" not in st.session_state:
    st.session_state.model_request_count = 0


def selection_key(job_id: str) -> str:
    """Give each job checkbox a short, stable Streamlit widget key."""

    digest = hashlib.sha256(job_id.encode("utf-8")).hexdigest()[:16]
    return f"selected-job-{digest}"


def selected_job_ids() -> list[str]:
    """Jobs checked in '我的岗位' become candidates for resume analysis."""

    return [
        job_id
        for job_id in st.session_state.saved_jobs
        if job_id in st.session_state.chosen_job_ids
    ]


def add_job(job: dict) -> bool:
    """Save one job in this session without adding duplicates."""

    if job["id"] in st.session_state.saved_jobs:
        return False
    fingerprint = "".join(str(job["jd_text"]).split()).casefold()
    if any(
        "".join(str(saved["jd_text"]).split()).casefold() == fingerprint
        for saved in st.session_state.saved_jobs.values()
    ):
        return False
    st.session_state.saved_jobs[job["id"]] = job
    return True


def remove_job(job_id: str) -> None:
    """Remove one recoverable session-only job and its selection state."""

    st.session_state.saved_jobs.pop(job_id, None)
    st.session_state.chosen_job_ids = [
        chosen for chosen in st.session_state.chosen_job_ids if chosen != job_id
    ]
    st.session_state.pop(selection_key(job_id), None)
    if st.session_state.get("match_job_id") == job_id:
        st.session_state.match_job_id = None


def select_all_jobs(checked: bool) -> None:
    """The two bulk buttons update checkbox values before the page reruns."""

    st.session_state.chosen_job_ids = (
        list(st.session_state.saved_jobs) if checked else []
    )
    for job_id in st.session_state.saved_jobs:
        st.session_state[selection_key(job_id)] = checked


def sync_job_selection(job_id: str) -> None:
    """Keep a durable shortlist when checkbox widgets leave the screen."""

    chosen = set(st.session_state.chosen_job_ids)
    if st.session_state[selection_key(job_id)]:
        chosen.add(job_id)
    else:
        chosen.discard(job_id)
    st.session_state.chosen_job_ids = list(chosen)


def open_page(page: str) -> None:
    """Navigate after a button click."""

    st.session_state.active_page = page


def open_analysis(mode: str) -> None:
    """Open the analysis center in the mode explicitly chosen by the user."""

    st.session_state.analysis_mode = mode
    st.session_state.active_page = "分析中心"


def group_cache_id(jobs: list[dict]) -> str:
    """Invalidate a cached portrait if a selected JD changes."""

    parts = [
        f"{job['id']}:{hashlib.sha256(job['jd_text'].encode('utf-8')).hexdigest()}"
        for job in jobs
    ]
    return hashlib.sha256("\n".join(sorted(parts)).encode("utf-8")).hexdigest()


def reset_consent(key: str) -> None:
    """Changing outgoing text requires a fresh, explicit confirmation."""

    st.session_state[key] = False


def reserve_model_request() -> bool:
    """Apply a small beta safeguard before sending anything to DeepSeek."""

    if st.session_state.model_request_count >= MAX_MODEL_REQUESTS_PER_SESSION:
        st.error(
            f"当前浏览会话已达到 {MAX_MODEL_REQUESTS_PER_SESSION} 次模型请求上限。"
            "这是公开测试阶段的费用保护。"
        )
        return False
    st.session_state.model_request_count += 1
    return True


def deepseek_is_configured() -> bool:
    """Check both local dotenv and root-level Streamlit Cloud Secrets."""

    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


def show_missing_deepseek_key() -> None:
    """Explain the two supported secret locations without exposing a key."""

    st.error(
        "应用尚未配置 DeepSeek API Key。本地运行请写入 .env；"
        "线上部署请写入 Streamlit Secrets，不要把 Key 提交到 Git。"
    )


def reset_resume_consent() -> None:
    """Ask for confirmation again if the outgoing resume text changes."""

    st.session_state.resume_consent = False


def show_target_job(job: dict) -> None:
    """Make the target of a paid analysis easy to verify."""

    with st.container(border=True):
        st.subheader(job["title"])
        st.write(f"{job['company']} · {job['location']}")
        details = [f"来源：{job['source']}"]
        if job["published_at"]:
            details.append(f"发布于 {job['published_at']}")
        st.caption(" · ".join(details))
        if job["url"]:
            st.link_button("查看来源页面", job["url"], key=f"target-link-{job['id']}")
        with st.expander("核对完整岗位 JD"):
            st.text_area(
                "岗位原文",
                value=job["jd_text"],
                height=240,
                disabled=True,
                key=f"target-jd-{job['id']}",
            )


def show_feedback(feedback: dict, job: dict) -> None:
    """Show human-readable advice, not the model's internal JSON."""

    st.subheader("简历与岗位的对照建议")
    with st.container(border=True):
        st.write(feedback["summary"])

    left, right = st.columns(2)
    with left:
        st.markdown("#### 已有依据的匹配点")
        if not feedback["matched_points"]:
            st.info("暂时没有找到能直接核对的匹配证据。")
        for point in feedback["matched_points"]:
            with st.expander(point["requirement"]):
                st.write("岗位原文：", point["jd_quote"])
                st.write("简历原文：", point["resume_quote"])

    with right:
        st.markdown("#### 简历还没清楚体现的要求")
        if not feedback["gaps"]:
            st.info("暂时没有发现明确缺口。")
        for gap in feedback["gaps"]:
            with st.expander(gap["requirement"]):
                st.write(gap["explanation"])
                st.write("岗位原文：", gap["jd_quote"])

    st.caption("“简历未体现”不等于“你不会”；请结合真实经历核对建议，不要编造技能或项目。")
    with st.container(border=True):
        st.markdown("#### 下一步可以做什么")
        if feedback["resume_edits"]:
            st.write("**先改简历表达**")
            for number, suggestion in enumerate(feedback["resume_edits"], start=1):
                st.write(f"{number}. {suggestion}")
        if feedback["learning_priorities"]:
            st.write("**再准备这些能力**")
            for number, priority in enumerate(feedback["learning_priorities"], start=1):
                st.write(f"{number}. {priority}")
        if not feedback["resume_edits"] and not feedback["learning_priorities"]:
            st.write("暂无足够依据给出进一步建议，请人工核对岗位要求。")
    report = build_single_resume_report(ResumeFeedback.model_validate(feedback), job)
    st.download_button(
        "下载可读报告（TXT）",
        data=report,
        file_name=report_filename(job["title"], "单岗位建议"),
        mime="text/plain",
        key=f"download-single-{job['id']}",
    )


def signal_coverage(signal) -> int:
    """Count each job at most once for one normalized requirement."""

    return len({item.job_id for item in signal.evidence})


def show_group_profile(profile: JobGroupProfile, jobs: list[dict]) -> None:
    """Present the verified portrait as readable evidence, never raw JSON."""

    job_map = {job["id"]: job for job in jobs}
    total = len(profile.job_ids) or len(jobs)
    st.subheader(profile.direction_name)
    st.write(profile.summary)
    st.caption(profile.consistency_summary)

    if profile.outlier_job_ids:
        names = [
            job_map[job_id]["title"]
            for job_id in profile.outlier_job_ids
            if job_id in job_map
        ]
        if names:
            st.warning("可能混入不同方向的岗位：" + "、".join(names) + "。建议核对后重新选择。")

    if not profile.signals:
        st.info("这组 JD 没有提取出可核对的共同要求，请调整样本后再试。")
        return

    ordered = sorted(
        profile.signals,
        key=lambda signal: (-signal_coverage(signal), signal.category, signal.label),
    )
    frequent = [
        signal
        for signal in ordered
        if signal_coverage(signal) >= 2 and signal_coverage(signal) / total >= 0.5
    ]
    other = [signal for signal in ordered if signal not in frequent]

    def render_signals(signals) -> None:
        for signal in signals:
            count = signal_coverage(signal)
            percent = round(count / total * 100)
            with st.container(border=True):
                st.markdown(f"**{signal.label}**")
                st.caption(f"{signal.category} · {count}/{total} 个岗位提到 · 约 {percent}%")
                with st.expander("查看对应 JD 依据"):
                    for evidence in signal.evidence:
                        job = job_map.get(evidence.job_id)
                        if job:
                            st.write(f"**{job['title']} · {job['company']}**")
                            st.write(f"“{evidence.quote}”")

    st.markdown("### 高频岗位信号")
    if frequent:
        render_signals(frequent)
    else:
        st.info("当前样本没有达到一半岗位都提及、且至少出现两次的要求。")
    if other:
        st.markdown("### 其他明确要求")
        render_signals(other)
    st.caption("频率只表示在本次所选样本中出现的次数，不等于要求的重要程度，也不代表整个行业。")
    st.download_button(
        "下载岗位方向画像（TXT）",
        data=build_group_profile_report(profile, jobs),
        file_name=report_filename(profile.direction_name, "岗位方向画像"),
        mime="text/plain",
        key=f"download-profile-{hashlib.sha256('|'.join(profile.job_ids).encode('utf-8')).hexdigest()[:12]}",
    )


def show_group_resume_feedback(
    feedback: dict, profile: JobGroupProfile
) -> None:
    """Show resume advice with group frequency context."""

    signal_map = {signal.label: signal for signal in profile.signals}
    total = len(profile.job_ids)
    st.subheader("简历与岗位方向的对照建议")
    with st.container(border=True):
        st.write(feedback["summary"])

    matched_col, gap_col = st.columns(2)
    with matched_col:
        st.markdown("#### 简历已有依据")
        if not feedback["matched_capabilities"]:
            st.info("暂时没有找到能直接核对的匹配证据。")
        for item in feedback["matched_capabilities"]:
            signal = signal_map[item["requirement"]]
            with st.expander(item["requirement"]):
                st.caption(f"本次样本中 {signal_coverage(signal)}/{total} 个岗位提到")
                st.write(item["explanation"])
                st.write("简历原文：", item["resume_quote"])

    with gap_col:
        st.markdown("#### 简历还没清楚体现")
        if not feedback["gaps"]:
            st.info("暂时没有发现明确缺口。")
        for item in feedback["gaps"]:
            signal = signal_map[item["requirement"]]
            with st.expander(item["requirement"]):
                st.caption(f"本次样本中 {signal_coverage(signal)}/{total} 个岗位提到")
                st.write(item["explanation"])

    action_col, edit_col = st.columns(2)
    with action_col:
        st.markdown("#### 准备顺序")
        for number, action in enumerate(feedback["action_plan"], start=1):
            st.write(f"{number}. {action}")
        if not feedback["action_plan"]:
            st.write("暂无足够依据安排准备顺序。")
    with edit_col:
        st.markdown("#### 简历表达建议")
        for suggestion in feedback["resume_edits"]:
            st.write("•", suggestion)
        if not feedback["resume_edits"]:
            st.write("暂无需要优先调整的表达。")
    st.caption("“未体现”不等于“不会”。只补充真实经历，不要根据建议编造项目、技能或数字。")
    typed_feedback = GroupResumeFeedback.model_validate(feedback)
    st.download_button(
        "下载方向简历建议（TXT）",
        data=build_group_resume_report(typed_feedback, profile),
        file_name=report_filename(profile.direction_name, "方向简历建议"),
        mime="text/plain",
        key=f"download-group-feedback-{hashlib.sha256(typed_feedback.summary.encode('utf-8')).hexdigest()[:12]}",
    )


def show_group_request_error(error: Exception, result_name: str) -> None:
    """Translate model failures without exposing submitted JD or resume text."""

    if isinstance(error, AuthenticationError):
        st.error("DeepSeek 拒绝了 API Key。请检查本地 .env 或线上 Secrets 中的 Key 是否有效。")
    elif isinstance(error, RateLimitError):
        st.error("DeepSeek 返回请求频率限制。请稍后再试，避免连续点击。")
    elif isinstance(error, APIConnectionError):
        st.error("当前无法连接 DeepSeek，请检查网络或稍后再试。")
    elif isinstance(error, APIStatusError):
        if error.status_code == 402:
            st.error("DeepSeek 返回 HTTP 402：可调用余额不足。")
        else:
            st.error(f"DeepSeek 返回 HTTP {error.status_code}。请记录这个状态码。")
    elif isinstance(error, GroupAnalysisFormatError):
        st.error(str(error))
    elif isinstance(error, ValidationError):
        st.error(f"模型返回了{result_name}，但内部结构无法安全使用。请不要连续点击。")
    elif isinstance(error, ValueError):
        st.error(str(error))
    elif isinstance(error, RuntimeError):
        st.error(str(error))
    else:
        st.error(f"生成{result_name}时出现其他错误，请稍后再试。")


def request_group_profile(jobs: list[dict], profile_id: str) -> None:
    """One explicit click makes one request for the selected JD group."""

    if not reserve_model_request():
        return
    try:
        profile = analyze_job_group(jobs)
        st.session_state.group_profiles[profile_id] = profile.model_dump()
    except (
        AuthenticationError,
        RateLimitError,
        APIConnectionError,
        APIStatusError,
        GroupAnalysisFormatError,
        ValidationError,
        ValueError,
        RuntimeError,
        OpenAIError,
    ) as error:
        show_group_request_error(error, "岗位方向画像")


def request_group_feedback(
    profile: JobGroupProfile, resume_text: str, feedback_id: str
) -> None:
    """One explicit click compares the resume with the cached group portrait."""

    if not reserve_model_request():
        return
    try:
        feedback = match_resume_to_group(profile, resume_text)
        st.session_state.group_feedback[feedback_id] = feedback.model_dump()
    except (
        AuthenticationError,
        RateLimitError,
        APIConnectionError,
        APIStatusError,
        GroupAnalysisFormatError,
        ValidationError,
        ValueError,
        RuntimeError,
        OpenAIError,
    ) as error:
        show_group_request_error(error, "简历对照结果")


def request_feedback(job_id: str, resume_text: str, feedback_id: str) -> None:
    """One explicit click makes one model request for both JD and resume."""

    if not reserve_model_request():
        return
    try:
        result = match_resume(st.session_state.saved_jobs[job_id]["jd_text"], resume_text)
        st.session_state.feedback[feedback_id] = result.model_dump()
    except AuthenticationError:
        st.error("DeepSeek 拒绝了 API Key。请检查本地 .env 或线上 Secrets 中的 Key 是否有效。")
    except RateLimitError:
        st.error("DeepSeek 返回请求频率限制。请稍后再试，避免连续点击。")
    except APIConnectionError:
        st.error("当前无法连接 DeepSeek，请检查网络或稍后再试。")
    except APIStatusError as error:
        if error.status_code == 402:
            st.error("DeepSeek 返回 HTTP 402：可调用余额不足。")
        elif error.status_code in (400, 422):
            st.error(
                f"DeepSeek 返回 HTTP {error.status_code}：请求参数被拒绝。"
                "这是程序需要排查的问题，请不要反复点击。"
            )
        else:
            st.error(f"DeepSeek 返回 HTTP {error.status_code}。请记录这个状态码。")
    except ValidationError:
        st.error("模型已返回内容，但内部字段格式不正确。请不要反复点击。")
    except FeedbackFormatError:
        st.error("模型返回的内容不完整或格式异常，本次没有生成可用建议；程序不会自动重试。")
    except RuntimeError as error:
        st.error(str(error))
    except ValueError as error:
        if "证据" in str(error):
            st.error("模型给出的证据无法在原文核对；本次没有生成可用建议。")
        else:
            st.error(str(error))
    except OpenAIError:
        st.error("DeepSeek 调用出现其他错误，请稍后再试。")


def render_manual_add() -> None:
    st.write("适用于任何行业：把在 BOSS 或其他渠道看到的岗位描述粘贴进来。这里不会自动访问该链接。")
    with st.form("add_manual_job"):
        note = st.text_input("岗位名称或备注（可选）", placeholder="例如：某公司内容运营专员")
        company = st.text_input("公司（可选）", placeholder="填写后可查看已选样本的公司分布")
        source_url = st.text_input("来源链接（可选）", placeholder="方便日后回到原岗位页")
        jd_text = st.text_area(
            "岗位 JD",
            height=240,
            max_chars=MAX_MANUAL_JD_CHARS,
            placeholder="粘贴岗位职责和任职要求",
        )
        added = st.form_submit_button("加入我的岗位")

    if not added:
        return
    cleaned_jd = jd_text.strip()
    parsed_url = urlparse(source_url.strip())
    if not cleaned_jd:
        st.error("请先填写岗位 JD。")
    elif source_url.strip() and (
        parsed_url.scheme not in ("http", "https") or not parsed_url.netloc
    ):
        st.error("来源链接需要是以 http:// 或 https:// 开头的完整网址。")
    else:
        digest = hashlib.sha256(cleaned_jd.encode("utf-8")).hexdigest()[:16]
        job = {
            "id": f"manual:{digest}",
            "source": "手动添加",
            "title": note.strip() or "手动添加的岗位",
            "company": company.strip() or "未填写",
            "location": "未提及",
            "jd_text": cleaned_jd,
            "url": source_url.strip(),
            "original_url": "",
            "published_at": "",
        }
        if add_job(job):
            st.toast("添加成功！可以继续添加，完成后到“我的岗位”查看。", icon="✅")
        else:
            st.info("相同内容的 JD 已经在列表里。")


def fetch_offer_page(offset: int) -> None:
    """Load one page for the last submitted filters, without calling DeepSeek."""

    query = st.session_state.search_query
    offerdao_key = os.getenv("OFFERDAO_API_KEY", "").strip()
    if not offerdao_key:
        offerdao_key = st.session_state.get("offerdao_test_key", "")
    if not offerdao_key:
        offerdao_key = get_public_test_key()
        st.session_state.offerdao_test_key = offerdao_key

    st.session_state.search_results = search_jobs(
        query["keyword"],
        city=query["city"],
        employment_type=query["employment_type"],
        api_key=offerdao_key,
        limit=OFFER_PAGE_SIZE,
        offset=offset,
    )


def render_offer_search() -> None:
    st.write("这个入口只查询 Offer岛，不抓取 BOSS；Offer岛主要面向 AI 方向，不能覆盖所有行业。")
    with st.form("search_jobs"):
        keyword = st.text_input("岗位关键词", placeholder="例如：运营、设计、财务、产品、开发", max_chars=50)
        city = st.text_input("城市（可选）", placeholder="例如：北京、上海、武汉")
        employment_type = st.selectbox("用工类型", ["不限", "实习", "正式"])
        submitted = st.form_submit_button("搜索岗位")

    if submitted:
        st.session_state.search_results = None
        if not keyword.strip():
            st.error("请填写岗位关键词。")
        else:
            st.session_state.search_query = {
                "keyword": keyword.strip(),
                "city": city.strip(),
                "employment_type": "" if employment_type == "不限" else employment_type,
            }
            try:
                fetch_offer_page(0)
            except (JobSourceError, ValueError) as error:
                st.error(str(error))

    results = st.session_state.get("search_results")
    if results is not None and (
        "search_query" not in st.session_state or "offset" not in results
    ):
        st.session_state.search_results = None
        results = None
        st.info("搜索功能已更新，请重新输入关键词并点击“搜索岗位”。")
    if results is not None:
        jobs = results["items"]
        query = st.session_state.search_query
        filters = [f"关键词：{query['keyword']}"]
        if query["city"]:
            filters.append(f"城市：{query['city']}")
        if query["employment_type"]:
            filters.append(f"类型：{query['employment_type']}")
        st.caption("本次搜索 · " + " · ".join(filters))

        offset = results["offset"]
        total = results["total"]
        page_number = offset // OFFER_PAGE_SIZE + 1
        companies = {
            job["company"] for job in jobs if job["company"] not in ("未提及", "未填写")
        }
        st.caption(
            f"Offer岛返回约 {total} 条 · 第 {page_number} 页显示 {len(jobs)} 条"
            f" · 本页来自 {len(companies)} 家已知公司。"
        )
        prev_col, next_col, _ = st.columns([1, 1, 5])
        with prev_col:
            if st.button("上一页", disabled=offset == 0):
                try:
                    fetch_offer_page(max(0, offset - OFFER_PAGE_SIZE))
                    st.rerun()
                except (JobSourceError, ValueError) as error:
                    st.error(str(error))
        with next_col:
            if st.button("下一页", disabled=offset + OFFER_PAGE_SIZE >= total):
                try:
                    fetch_offer_page(offset + OFFER_PAGE_SIZE)
                    st.rerun()
                except (JobSourceError, ValueError) as error:
                    st.error(str(error))

        if not jobs:
            st.info("这个来源没有返回岗位。可换关键词、去掉城市筛选，或粘贴其他渠道的 JD。")
        elif st.button("把本页岗位全部加入我的列表"):
            count = sum(add_job(job) for job in jobs)
            if count:
                st.toast(f"已加入 {count} 个岗位！可以继续搜索或翻页。", icon="✅")
            else:
                st.info("本页岗位都已经在列表里。")

        for job in jobs:
            with st.container(border=True):
                st.write(job["title"], "·", job["company"])
                st.caption(f"{job['location']} · 发布于 {job['published_at'] or '未注明'} · 来源：Offer岛")
                st.link_button("查看 Offer岛岗位页", job["url"], key=f"offer-link-{job['id']}")
                if job["original_url"]:
                    st.link_button("查看原始来源", job["original_url"], key=f"original-link-{job['id']}")
                with st.expander("查看 JD 内容"):
                    st.text(job["jd_text"])
                if st.button("加入我的岗位", key=f"add-{job['id']}"):
                    if add_job(job):
                        st.toast("添加成功！可以继续浏览岗位。", icon="✅")
                    else:
                        st.info("这个岗位已经在列表里。")

    st.caption("搜索使用共享测试 Key 或你自己的 Offer岛 Key；搜索本身不调用 DeepSeek。")


def render_find_page() -> None:
    st.subheader("先搜索并收集感兴趣的岗位")
    st.caption("优先自动搜索；如果没有搜到，或岗位来自 BOSS 等未接入来源，再手动粘贴 JD。")
    saved_count = st.empty()
    offer_tab, manual_tab = st.tabs(["自动搜索（Offer岛）", "手动添加 JD"])
    with offer_tab:
        render_offer_search()
    with manual_tab:
        render_manual_add()
    count = len(st.session_state.saved_jobs)
    if count:
        saved_count.caption(f"已加入 {count} 个岗位。可以继续添加；完成后点上方“我的岗位”勾选。")


def render_job_list() -> None:
    st.subheader("我的岗位")
    st.caption("加入的岗位会直接列在下面。勾选一个或多个，组成待分析清单。")
    saved_jobs = st.session_state.saved_jobs
    if not saved_jobs:
        st.info("这里还没有岗位。先到“找岗位”自动搜索；没有合适结果时再手动添加 JD。")
        st.button("去找岗位", on_click=open_page, args=("找岗位",))
        return

    choose_col, clear_col, _ = st.columns([1, 1, 6])
    with choose_col:
        st.button("全选", on_click=select_all_jobs, args=(True,), use_container_width=True)
    with clear_col:
        st.button("全不选", on_click=select_all_jobs, args=(False,), use_container_width=True)
    chosen_ids = selected_job_ids()
    st.caption(f"已勾选 {len(chosen_ids)} / {len(saved_jobs)} 个岗位")
    if chosen_ids:
        company_counts = Counter(
            saved_jobs[job_id]["company"]
            for job_id in chosen_ids
            if saved_jobs[job_id]["company"] not in ("未填写", "未提及")
        )
        st.write(f"这组样本：{len(chosen_ids)} 条岗位 · {len(company_counts)} 家已知公司")
        if company_counts:
            distribution = " · ".join(
                f"{company} {count} 条" for company, count in company_counts.most_common(5)
            )
            if len(company_counts) > 5:
                distribution += f" · 另有 {len(company_counts) - 5} 家公司"
            st.caption("公司分布：" + distribution)
        else:
            st.caption("目前没有可统计的公司信息；手动添加岗位时可以填写公司。")
        if len(chosen_ids) < 5:
            st.info("当前少于 5 条，可用来试流程；还不适合据此概括某类岗位的高频要求。")
        elif len(company_counts) <= 1:
            st.warning("样本来自同一家或未知公司，结论容易受单一公司影响。")
        st.caption("请勾选同一类型的岗位，并核对发布时间。样本数量和公司分布只是质量提示，不代表行业统计结论。")

    st.caption("勾选本身不会调用模型。多个同类岗位用于方向画像；具体投递时可以精读其中一条。")
    group_col, single_col, _ = st.columns([2, 2, 4])
    with group_col:
        st.button(
            f"分析岗位方向（已选 {len(chosen_ids)} 条）",
            type="primary",
            disabled=not 2 <= len(chosen_ids) <= MAX_GROUP_JOBS,
            on_click=open_analysis,
            args=("岗位方向画像",),
            use_container_width=True,
        )
    with single_col:
        st.button(
            "精读其中一个岗位",
            disabled=not chosen_ids,
            on_click=open_analysis,
            args=("单岗位精读",),
            use_container_width=True,
        )
    if len(chosen_ids) > MAX_GROUP_JOBS:
        st.warning(f"当前版本一次最多分析 {MAX_GROUP_JOBS} 条。请取消部分勾选后再生成岗位方向画像。")

    st.markdown("### 已加入的岗位")
    for job_id, job in saved_jobs.items():
        key = selection_key(job_id)
        if key not in st.session_state:
            st.session_state[key] = job_id in st.session_state.chosen_job_ids
        with st.container(border=True):
            check_col, content_col = st.columns([1, 16], vertical_alignment="top")
            with check_col:
                st.checkbox(
                    f"选择{job['title']}",
                    key=key,
                    label_visibility="collapsed",
                    on_change=sync_job_selection,
                    args=(job_id,),
                )
            with content_col:
                st.subheader(job["title"])
                st.write(f"{job['company']} · {job['location']}")
                details = [f"来源：{job['source']}"]
                if job["published_at"]:
                    details.append(f"发布于 {job['published_at']}")
                st.caption(" · ".join(details))
                preview = job["jd_text"].replace("\n", " ")
                st.write(preview[:170] + ("…" if len(preview) > 170 else ""))
                with st.expander("查看完整 JD"):
                    st.write(job["jd_text"])
                link_col, remove_col, _ = st.columns([2, 1, 7])
                with link_col:
                    if job["url"]:
                        st.link_button("查看来源页面", job["url"], key=f"list-link-{job_id}")
                with remove_col:
                    st.button(
                        "移除",
                        key=f"remove-{job_id}",
                        on_click=remove_job,
                        args=(job_id,),
                    )

    st.caption("清单只保存在当前浏览会话中，关闭或重启后可能消失。")


def render_single_analysis_page() -> None:
    st.subheader("精读一个岗位")
    chosen_ids = selected_job_ids()
    if not chosen_ids:
        st.info("还没有勾选待分析岗位。请先到“我的岗位”勾选至少一条。")
        st.button("去我的岗位", on_click=open_page, args=("我的岗位",), key="single-back-jobs")
        return

    st.caption(f"待分析清单中有 {len(chosen_ids)} 个岗位。一次只分析一条，不会自动批量收费。")
    if st.session_state.get("match_job_id") not in chosen_ids:
        st.session_state.match_job_id = None
    job_id = st.selectbox(
        "本次要分析的岗位",
        chosen_ids,
        index=None,
        placeholder="请确认本次要分析哪一条岗位",
        format_func=lambda value: (
            f"{st.session_state.saved_jobs[value]['title']} · "
            f"{st.session_state.saved_jobs[value]['source']}"
        ),
        key="match_job_id",
    )
    if job_id is None:
        st.info("选择岗位后再上传简历。选岗本身不会调用模型。")
        return

    if st.session_state.get("last_match_job_id") != job_id:
        st.session_state.last_match_job_id = job_id
        st.session_state.resume_consent = False
    job = st.session_state.saved_jobs[job_id]
    show_target_job(job)

    st.subheader("上传并检查简历")
    uploaded_file = st.file_uploader(
        "上传简历（PDF 或 DOCX，最多 5 MB）",
        type=["pdf", "docx"],
        max_upload_size=5,
    )
    if uploaded_file is None:
        if st.session_state.get("resume_file_digest"):
            for key in ("resume_file_digest", "resume_text", "resume_error", "resume_consent"):
                st.session_state.pop(key, None)
        return

    file_bytes = uploaded_file.getvalue()
    file_digest = hashlib.sha256(file_bytes).hexdigest()
    if file_digest != st.session_state.get("resume_file_digest"):
        st.session_state.resume_file_digest = file_digest
        st.session_state.resume_consent = False
        try:
            extracted = extract_resume_text(uploaded_file.name, file_bytes)
            st.session_state.resume_text = redact_basic_contacts(extracted)
            st.session_state.resume_error = ""
        except ResumeReadError as error:
            st.session_state.resume_text = ""
            st.session_state.resume_error = str(error)

    if st.session_state.get("resume_error"):
        st.error(st.session_state.resume_error)
        return
    if not st.session_state.get("resume_text"):
        return

    st.text_area(
        "将发送给模型的简历文字（可以删去姓名、地址等信息）",
        height=260,
        max_chars=16000,
        key="resume_text",
        on_change=reset_resume_consent,
    )
    st.caption("已尝试遮盖常见邮箱、手机号和证件号；仍需你检查。扫描版 PDF 暂不支持。")
    consent = st.checkbox(
        f"我已核对目标岗位“{job['title']}”和简历文字，"
        "同意发送给 DeepSeek 生成建议（可能产生费用）",
        key="resume_consent",
    )
    edited_resume = st.session_state.resume_text.strip()
    feedback_id = job_id + ":" + hashlib.sha256(edited_resume.encode("utf-8")).hexdigest()
    feedback = st.session_state.feedback.get(feedback_id)
    if feedback is None:
        st.caption("点击后会在一次调用中先整理岗位要求，再对照简历；不会先单独收费分析 JD。")
        if st.button("生成对照建议", type="primary"):
            if not edited_resume:
                st.error("简历文字不能为空。")
            elif not consent:
                st.warning("请先检查文字并勾选确认，再调用模型。")
            elif not deepseek_is_configured():
                show_missing_deepseek_key()
            else:
                with st.spinner("正在整理岗位要求并对照简历，请稍候……"):
                    request_feedback(job_id, edited_resume, feedback_id)
        feedback = st.session_state.feedback.get(feedback_id)
    else:
        st.success("这份岗位与简历的建议已生成；本次不会重复调用或重复收费。")

    if feedback:
        show_feedback(feedback, job)


def render_group_resume_section(profile: JobGroupProfile, profile_id: str) -> None:
    """Let the user optionally make a second, explicit group-to-resume request."""

    st.divider()
    st.subheader("再与简历对照（可选）")
    st.caption("岗位画像已经生成。只有继续上传简历并点击生成，才会发起第二次 DeepSeek 请求。")
    if not profile.signals:
        st.info("当前岗位画像没有可用于对照的要求，请先调整岗位样本。")
        return

    digest_key = f"group-resume-digest-{profile_id}"
    text_key = f"group-resume-text-{profile_id}"
    error_key = f"group-resume-error-{profile_id}"
    consent_key = f"group-resume-consent-{profile_id}"
    uploaded_file = st.file_uploader(
        "上传简历（PDF 或 DOCX，最多 5 MB）",
        type=["pdf", "docx"],
        max_upload_size=5,
        key=f"group-resume-file-{profile_id}",
    )
    if uploaded_file is None:
        return

    file_bytes = uploaded_file.getvalue()
    file_digest = hashlib.sha256(file_bytes).hexdigest()
    if file_digest != st.session_state.get(digest_key):
        st.session_state[digest_key] = file_digest
        st.session_state[consent_key] = False
        try:
            extracted = extract_resume_text(uploaded_file.name, file_bytes)
            st.session_state[text_key] = redact_basic_contacts(extracted)
            st.session_state[error_key] = ""
        except ResumeReadError as error:
            st.session_state[text_key] = ""
            st.session_state[error_key] = str(error)

    if st.session_state.get(error_key):
        st.error(st.session_state[error_key])
        return
    if not st.session_state.get(text_key):
        return

    st.text_area(
        "将发送给模型的简历文字（可以继续删除个人信息）",
        height=260,
        max_chars=16000,
        key=text_key,
        on_change=reset_consent,
        args=(consent_key,),
    )
    st.caption("程序已尝试遮盖常见联系方式，但仍需要你亲自检查剩余文字。")
    consent = st.checkbox(
        f"我已核对简历文字，同意将它与“{profile.direction_name}”岗位画像发送给 DeepSeek"
        "生成建议（这是第二次请求，可能产生费用）",
        key=consent_key,
    )
    edited_resume = st.session_state[text_key].strip()
    feedback_id = profile_id + ":" + hashlib.sha256(edited_resume.encode("utf-8")).hexdigest()
    feedback = st.session_state.group_feedback.get(feedback_id)
    if feedback is None:
        if st.button("生成方向简历建议", type="primary", key=f"group-match-{profile_id}"):
            if not edited_resume:
                st.error("简历文字不能为空。")
            elif not consent:
                st.warning("请先检查文字并勾选确认，再调用模型。")
            elif not deepseek_is_configured():
                show_missing_deepseek_key()
            else:
                with st.spinner("正在把简历与岗位方向画像对照，请稍候……"):
                    request_group_feedback(profile, edited_resume, feedback_id)
        feedback = st.session_state.group_feedback.get(feedback_id)
    else:
        st.success("这份简历与岗位方向的建议已生成；相同组合不会重复调用。")

    if feedback:
        show_group_resume_feedback(feedback, profile)


def render_group_analysis_page() -> None:
    """Build the product's primary multi-JD direction portrait."""

    chosen_ids = selected_job_ids()
    if len(chosen_ids) < 2:
        st.info("岗位方向画像至少需要 2 条 JD；建议选择 5 至 10 条同类岗位。")
        st.button("去我的岗位", on_click=open_page, args=("我的岗位",), key="group-back-jobs")
        return
    if len(chosen_ids) > MAX_GROUP_JOBS:
        st.warning(f"当前版本一次最多分析 {MAX_GROUP_JOBS} 条岗位，请先缩小样本。")
        st.button("调整岗位样本", on_click=open_page, args=("我的岗位",), key="group-adjust-jobs")
        return

    jobs = [st.session_state.saved_jobs[job_id] for job_id in chosen_ids]
    profile_id = group_cache_id(jobs)
    companies = {
        job["company"] for job in jobs if job["company"] not in ("未填写", "未提及")
    }

    st.subheader("岗位方向画像")
    st.caption("先从多份同类 JD 中找出重复要求，再决定是否用简历进行方向对照。")
    metric_jobs, metric_companies, metric_cost = st.columns(3)
    metric_jobs.metric("岗位样本", f"{len(jobs)} 条")
    metric_companies.metric("已知公司", f"{len(companies)} 家")
    metric_cost.metric("本步模型请求", "1 次")
    if len(jobs) < 5:
        st.info("当前样本少于 5 条，报告适合试流程和初步对比，不宜当作行业结论。")
    if len(companies) <= 1:
        st.warning("样本来自同一家或公司信息不足，方向画像可能偏向单一公司的要求。")

    with st.expander("核对本次岗位样本"):
        for number, job in enumerate(jobs, start=1):
            st.write(f"{number}. **{job['title']}** · {job['company']} · {job['source']}")

    profile_data = st.session_state.group_profiles.get(profile_id)
    if profile_data is None:
        consent_key = f"group-profile-consent-{profile_id}"
        consent = st.checkbox(
            f"我已核对以上 {len(jobs)} 条岗位大体属于同一方向，同意将这些 JD 发送给 DeepSeek"
            " 生成岗位画像（可能产生费用）",
            key=consent_key,
        )
        st.caption("本次只生成岗位方向画像，不会上传或分析简历；程序不会自动重试。")
        if st.button("生成岗位方向画像", type="primary", key=f"build-group-{profile_id}"):
            if not consent:
                st.warning("请先核对样本并勾选确认，再调用模型。")
            elif not deepseek_is_configured():
                show_missing_deepseek_key()
            else:
                with st.spinner("正在归纳多份 JD 并核对共同要求，请稍候……"):
                    request_group_profile(jobs, profile_id)
        profile_data = st.session_state.group_profiles.get(profile_id)
    else:
        st.success("这组岗位的方向画像已生成；样本未变化时不会重复调用。")

    if profile_data is None:
        return
    profile = JobGroupProfile.model_validate(profile_data)
    show_group_profile(profile, jobs)
    render_group_resume_section(profile, profile_id)


def render_analysis_center() -> None:
    """Offer two related analysis depths without giving them equal priority."""

    if st.session_state.get("analysis_mode") not in ("岗位方向画像", "单岗位精读"):
        st.session_state.analysis_mode = "岗位方向画像"
    st.segmented_control(
        "分析方式",
        ["岗位方向画像", "单岗位精读"],
        required=True,
        key="analysis_mode",
    )
    remaining = MAX_MODEL_REQUESTS_PER_SESSION - st.session_state.model_request_count
    st.caption(
        f"公开测试费用保护：当前浏览会话还可主动发起 {max(0, remaining)} 次模型请求。"
        "失败请求也会计入，避免连续重试。"
    )
    st.divider()
    if st.session_state.analysis_mode == "岗位方向画像":
        render_group_analysis_page()
    else:
        render_single_analysis_page()


def render_home_page() -> None:
    """A calm starting page that can later sit in front of account sign-in."""

    st.markdown(
        """
        <section class="hero">
            <div class="hero-eyebrow">JOB DIRECTION · EVIDENCE FIRST</div>
            <h1>别只读一份 JD。<br>先看清一个岗位方向。</h1>
            <p>收集多个真实岗位，找出反复出现的职责与能力要求；再把这些有原文依据的岗位信号，与你的简历逐项对照。</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    start_col, continue_col, _ = st.columns([2, 2, 4])
    with start_col:
        st.button(
            "开始收集岗位",
            type="primary",
            on_click=open_page,
            args=("找岗位",),
            use_container_width=True,
        )
    with continue_col:
        st.button(
            f"查看我的岗位（{len(st.session_state.saved_jobs)}）",
            on_click=open_page,
            args=("我的岗位",),
            disabled=not st.session_state.saved_jobs,
            use_container_width=True,
        )

    st.markdown('<div class="section-kicker">WHAT YOU GET</div>', unsafe_allow_html=True)
    st.subheader("从零散招聘信息，到可执行的准备方向")
    feature_one, feature_two, feature_three = st.columns(3)
    with feature_one:
        with st.container(border=True):
            st.markdown("#### 01 · 岗位方向画像")
            st.write("汇总 2–10 份同类 JD，识别高频职责、能力、工具和硬性条件。")
    with feature_two:
        with st.container(border=True):
            st.markdown("#### 02 · 原文依据")
            st.write("每项结论都能展开查看来自哪条岗位，频率由程序计算，不展示虚假匹配分。")
    with feature_three:
        with st.container(border=True):
            st.markdown("#### 03 · 两种简历对照")
            st.write("既能面向整个岗位方向制定计划，也能在真正投递前精读某一个岗位。")

    st.markdown('<div class="section-kicker">HOW IT WORKS</div>', unsafe_allow_html=True)
    with st.container(border=True):
        step_one, step_two, step_three = st.columns(3)
        step_one.markdown("**1　收集**  \n自动搜索，或手动加入其他平台的 JD。")
        step_two.markdown("**2　筛选**  \n勾选同类岗位，并检查公司与样本数量。")
        step_three.markdown("**3　分析**  \n先生成方向画像，再按需要对照简历。")
    st.caption("浏览、搜索、添加和勾选都不会调用 DeepSeek。每一次可能产生费用的请求都会提前说明并要求确认。")


def render_guide_content() -> None:
    st.write("1. 在“找岗位”优先自动搜索；未搜到时再手动添加 JD。")
    st.write("2. 到“我的岗位”勾选同类岗位，建议来自不同公司。")
    st.write("3. 在“分析中心”生成岗位方向画像，或精读其中一个岗位。")
    st.caption("每次调用 DeepSeek 前都会单独说明并要求确认；浏览、添加和勾选不会调用。")


def render_privacy_content() -> None:
    st.markdown("**数据去向**")
    st.write("搜索词会发送给 Offer岛；只有在你勾选确认并点击生成后，JD 或简历文字才会发送给 DeepSeek。")
    st.write("简历先在当前服务中提取文字并遮盖常见联系方式，你仍需检查姓名、地址等剩余信息。")
    st.markdown("**保存与费用**")
    st.write("当前版本不设数据库，岗位、简历文字和结果只保留在当前浏览会话中。")
    st.write("模型请求可能消耗网站维护者的 API 额度；页面会在每次请求前提示，刷新页面不能替代平台端消费上限。")
    st.caption("请勿上传不愿交给第三方模型处理的敏感、机密或他人资料。")


brand_html = '<div class="brand-mark"><span class="brand-dot"></span><span>求职对照台</span></div>'

with st.container(key="desktop-header"):
    brand_col, guide_col, privacy_col, account_col = st.columns(
        [5.2, 1.15, 1.45, 1.8], vertical_alignment="center"
    )
    with brand_col:
        st.markdown(brand_html, unsafe_allow_html=True)
    with guide_col:
        with st.popover("使用指南"):
            render_guide_content()
    with privacy_col:
        with st.popover("隐私与费用"):
            render_privacy_content()
    with account_col:
        st.button(
            "访客模式 · 登录待开放",
            disabled=True,
            help="这里已为后续用户登录和跨设备保存预留位置。",
            use_container_width=True,
        )

with st.container(key="mobile-header"):
    mobile_brand_col, mobile_help_col = st.columns([3.2, 1], vertical_alignment="center")
    with mobile_brand_col:
        st.markdown(brand_html, unsafe_allow_html=True)
    with mobile_help_col:
        with st.popover("说明", use_container_width=True):
            st.markdown("#### 使用流程")
            render_guide_content()
            st.divider()
            st.markdown("#### 隐私与费用")
            render_privacy_content()

page = st.segmented_control(
    "页面",
    ["首页", "找岗位", "我的岗位", "分析中心"],
    required=True,
    key="active_page",
    label_visibility="collapsed",
)
st.divider()
if page == "首页":
    render_home_page()
elif page == "找岗位":
    render_find_page()
elif page == "我的岗位":
    render_job_list()
else:
    render_analysis_center()

st.divider()
st.caption("公开测试版：结果可能遗漏或出错，不等于录用判断；岗位、简历和反馈没有长期保存。")
