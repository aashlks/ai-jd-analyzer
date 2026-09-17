"""Define the fixed JSON structures returned by the LLM."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JobAnalysis(BaseModel):
    """Fields shared by technical and non-technical job descriptions."""

    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(description="岗位名称；JD 未提及时填写“未提及”")
    company: str = Field(description="公司名称；JD 未提及时填写“未提及”")
    employment_type: str = Field(description="实习、正式、兼职等；未提及时填写“未提及”")
    location: str = Field(description="工作地点；JD 未提及时填写“未提及”")
    responsibilities: list[str] = Field(description="JD 明确写出的主要工作职责")
    required_skills: list[str] = Field(
        description="明确要求的专业能力、通用能力或工具，不限技术岗位"
    )
    other_requirements: list[str] = Field(
        description="明确写出的其他硬性条件，如资格证书、语言或出差要求"
    )
    education_requirement: str = Field(
        description="学历或年级要求；JD 未提及时填写“未提及”"
    )
    experience_requirement: str = Field(
        description="工作、项目或实习经验要求；未提及时填写“未提及”"
    )
    work_schedule: str = Field(
        description="出勤、工作时间、实习时长等安排；未提及时填写“未提及”"
    )
    bonus_points: list[str] = Field(description="JD 中明确写出的加分项或优先条件")


class MatchedPoint(BaseModel):
    """One requirement with a quote from both the JD and the resume."""

    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    jd_quote: str = Field(min_length=1)
    resume_quote: str = Field(min_length=1)


class GapPoint(BaseModel):
    """A JD requirement that the resume does not clearly demonstrate."""

    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    jd_quote: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class ResumeFeedback(BaseModel):
    """Evidence-based advice for one resume and one job description."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    matched_points: list[MatchedPoint]
    gaps: list[GapPoint]
    resume_edits: list[str]
    learning_priorities: list[str]


class JobEvidence(BaseModel):
    """One exact excerpt showing that a job mentions a normalized signal."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class GroupSignal(BaseModel):
    """A requirement or responsibility shared by one or more selected jobs."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    category: Literal[
        "岗位职责",
        "专业能力",
        "通用能力",
        "工具",
        "学历经验",
        "工作条件",
        "加分项",
        "其他要求",
    ]
    evidence: list[JobEvidence] = Field(min_length=1)


class JobGroupProfile(BaseModel):
    """Evidence-backed portrait of a group of related job descriptions."""

    model_config = ConfigDict(extra="forbid")

    direction_name: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    consistency_summary: str = Field(min_length=1)
    job_ids: list[str] = Field(default_factory=list)
    outlier_job_ids: list[str]
    signals: list[GroupSignal]


class GroupMatchedCapability(BaseModel):
    """A group-level requirement supported by an exact resume excerpt."""

    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    resume_quote: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class GroupGap(BaseModel):
    """A group-level requirement not clearly demonstrated in the resume."""

    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class GroupResumeFeedback(BaseModel):
    """Evidence-based resume advice for a selected job direction."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    matched_capabilities: list[GroupMatchedCapability]
    gaps: list[GroupGap]
    resume_edits: list[str]
    action_plan: list[str]
