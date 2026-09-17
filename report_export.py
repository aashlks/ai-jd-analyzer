"""Turn validated analysis objects into readable plain-text reports."""

import re

from models import GroupResumeFeedback, JobGroupProfile, ResumeFeedback


def _line(value: object) -> str:
    """Keep untrusted model or JD text on one readable plain-text line."""

    return " ".join(str(value).split())


def report_filename(label: str, suffix: str) -> str:
    """Create a short filename that is safe on Windows and common browsers."""

    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", _line(label)).strip(" ._")
    return f"{(cleaned or '求职分析')[:50]}-{suffix}.txt"


def build_group_profile_report(profile: JobGroupProfile, jobs: list[dict]) -> str:
    """Export a job-direction portrait with sample and evidence context."""

    job_map = {str(job["id"]): job for job in jobs}
    total = len(profile.job_ids) or len(jobs)
    lines = [
        "求职对照台｜岗位方向画像",
        "=" * 28,
        f"方向：{_line(profile.direction_name)}",
        f"概括：{_line(profile.summary)}",
        f"样本一致性：{_line(profile.consistency_summary)}",
        f"样本数：{total} 条",
        "",
        "【本次岗位样本】",
    ]
    for number, job in enumerate(jobs, start=1):
        lines.append(
            f"{number}. {_line(job.get('title', '未提及'))}｜"
            f"{_line(job.get('company', '未提及'))}｜{_line(job.get('source', '未提及'))}"
        )

    if profile.outlier_job_ids:
        names = [
            _line(job_map[job_id].get("title", job_id))
            for job_id in profile.outlier_job_ids
            if job_id in job_map
        ]
        if names:
            lines.extend(["", "【可能混入的不同方向岗位】", "、".join(names)])

    lines.extend(["", "【岗位信号与原文依据】"])
    ordered = sorted(
        profile.signals,
        key=lambda signal: (
            -len({item.job_id for item in signal.evidence}),
            signal.category,
            signal.label,
        ),
    )
    if not ordered:
        lines.append("本次没有提取出可核对的岗位信号。")
    for number, signal in enumerate(ordered, start=1):
        count = len({item.job_id for item in signal.evidence})
        lines.append(
            f"{number}. {_line(signal.label)}（{signal.category}，{count}/{total} 个岗位提到）"
        )
        for evidence in signal.evidence:
            job = job_map.get(evidence.job_id, {})
            lines.append(
                f"   - {_line(job.get('title', evidence.job_id))}｜"
                f"{_line(job.get('company', '未提及'))}：“{_line(evidence.quote)}”"
            )

    lines.extend(
        [
            "",
            "说明：频率只反映本次所选样本，不等于要求的重要程度，也不代表整个行业。",
            "结果由模型辅助整理，可能遗漏或出错，请回到原 JD 核对。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_group_resume_report(
    feedback: GroupResumeFeedback, profile: JobGroupProfile
) -> str:
    """Export readable resume advice for a verified job-direction portrait."""

    signal_map = {signal.label: signal for signal in profile.signals}
    total = len(profile.job_ids)
    lines = [
        "求职对照台｜简历与岗位方向对照",
        "=" * 30,
        f"岗位方向：{_line(profile.direction_name)}",
        f"总体建议：{_line(feedback.summary)}",
        "",
        "【简历已有依据】",
    ]
    if not feedback.matched_capabilities:
        lines.append("暂时没有找到能直接核对的匹配证据。")
    for item in feedback.matched_capabilities:
        signal = signal_map[item.requirement]
        count = len({evidence.job_id for evidence in signal.evidence})
        lines.append(f"- {_line(item.requirement)}（{count}/{total} 个岗位提到）")
        lines.append(f"  说明：{_line(item.explanation)}")
        lines.append(f"  简历原文：“{_line(item.resume_quote)}”")

    lines.extend(["", "【简历还没清楚体现】"])
    if not feedback.gaps:
        lines.append("暂时没有发现明确缺口。")
    for item in feedback.gaps:
        signal = signal_map[item.requirement]
        count = len({evidence.job_id for evidence in signal.evidence})
        lines.append(f"- {_line(item.requirement)}（{count}/{total} 个岗位提到）")
        lines.append(f"  {_line(item.explanation)}")

    lines.extend(["", "【准备顺序】"])
    lines.extend(
        f"{number}. {_line(action)}"
        for number, action in enumerate(feedback.action_plan, start=1)
    )
    if not feedback.action_plan:
        lines.append("暂无足够依据安排准备顺序。")

    lines.extend(["", "【简历表达建议】"])
    lines.extend(f"- {_line(item)}" for item in feedback.resume_edits)
    if not feedback.resume_edits:
        lines.append("暂无需要优先调整的表达。")

    lines.extend(
        [
            "",
            "说明：“未体现”不等于“不会”。只补充真实经历，不要编造项目、技能或数字。",
            "本报告可能遗漏或出错，不等于录用判断。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_single_resume_report(feedback: ResumeFeedback, job: dict) -> str:
    """Export readable evidence and advice for one target job."""

    lines = [
        "求职对照台｜单岗位简历精读",
        "=" * 27,
        f"岗位：{_line(job.get('title', '未提及'))}",
        f"公司：{_line(job.get('company', '未提及'))}",
        f"总体建议：{_line(feedback.summary)}",
        "",
        "【已有依据的匹配点】",
    ]
    if not feedback.matched_points:
        lines.append("暂时没有找到能直接核对的匹配证据。")
    for item in feedback.matched_points:
        lines.append(f"- {_line(item.requirement)}")
        lines.append(f"  岗位原文：“{_line(item.jd_quote)}”")
        lines.append(f"  简历原文：“{_line(item.resume_quote)}”")

    lines.extend(["", "【简历还没清楚体现的要求】"])
    if not feedback.gaps:
        lines.append("暂时没有发现明确缺口。")
    for item in feedback.gaps:
        lines.append(f"- {_line(item.requirement)}：{_line(item.explanation)}")
        lines.append(f"  岗位原文：“{_line(item.jd_quote)}”")

    lines.extend(["", "【简历表达建议】"])
    lines.extend(f"- {_line(item)}" for item in feedback.resume_edits)
    if not feedback.resume_edits:
        lines.append("暂无需要优先调整的表达。")

    lines.extend(["", "【能力准备重点】"])
    lines.extend(f"- {_line(item)}" for item in feedback.learning_priorities)
    if not feedback.learning_priorities:
        lines.append("暂无需要优先准备的能力。")

    lines.extend(
        [
            "",
            "说明：“未体现”不等于“不会”。只补充真实经历，不要编造项目、技能或数字。",
            "本报告可能遗漏或出错，不等于录用判断。",
        ]
    )
    return "\n".join(lines) + "\n"
