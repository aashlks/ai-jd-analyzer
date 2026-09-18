"""集中管理 Streamlit 网页的外观。

这里没有岗位、简历或 API 逻辑。修改数值并保存后，欢迎页和主工作区会一起更新。
CSS 尺寸要保留 ``px``、``rem`` 或 ``vw`` 等单位。
"""


# 颜色：想尝试另一套视觉风格时，优先修改这里的十六进制色值。
COLORS = {
    "ink": "#233247",
    "muted": "#718092",
    "blue": "#7998b2",
    "blue_dark": "#526f89",
    "blue_pale": "#eaf1f7",
    "blue_mist": "#f1f5f9",
    "line": "#dce6ee",
    "paper": "#ffffff",
    "canvas": "#f5f8fb",
    "landing_canvas": "#f2f6fa",
}


# 工作区通用尺寸：集中控制页面宽度、留白、卡片和按钮，不用去 web_app.py 到处找数字。
SIZES = {
    "app_max_width": "1160px",
    "app_top_padding": "1.15rem",
    "app_bottom_padding": "3.5rem",
    "header_min_height": "3.2rem",
    "section_gap": "1.25rem",
    "panel_radius": "18px",
    "panel_padding": "1.15rem",
    "panel_shadow": "0 12px 34px rgba(63, 86, 108, 0.055)",
    "button_height": "2.7rem",
    "button_radius": "11px",
    "input_radius": "10px",
    "metric_radius": "16px",
    "page_intro_padding": "1.45rem 1.6rem",
    "page_intro_radius": "20px",
    "page_title_size": "clamp(1.7rem, 3vw, 2.35rem)",
    "page_copy_width": "720px",
}


# 独立欢迎页尺寸：只影响用户首次进入时看到的全屏页面。
LANDING = {
    "landing_max_width": "1180px",
    "landing_min_height": "100vh",
    "landing_outer_padding": "clamp(1.25rem, 4vw, 3.5rem)",
    "landing_hero_padding": "clamp(2rem, 6vw, 5.25rem)",
    "landing_hero_radius": "32px",
    "landing_title_size": "clamp(3rem, 7vw, 6.6rem)",
    "landing_title_width": "980px",
    "landing_copy_width": "720px",
    "landing_cta_width": "260px",
    "landing_feature_radius": "18px",
    "landing_feature_min_height": "150px",
}


TYPOGRAPHY = {
    "body_font": '"Inter", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
    "body_size": "16px",
    "small_size": ".88rem",
    "body_line_height": "1.7",
}


# 各区块横向比例：只改数字即可；数字越大，对应列分到的空间越多。
COLUMN_RATIOS = {
    "desktop_header": [5.4, 1.15, 1.45, 1.8],
    "mobile_header": [3.2, 1],
    "pagination": [1, 1, 5],
    "shortlist_select": [1, 1, 6],
    "shortlist_actions": [2, 2, 4],
    "job_card": [1, 16],
    "job_card_actions": [2, 1, 7],
}


# 文本框高度是 Streamlit 控件参数，所以这里使用不带单位的像素数字。
COMPONENT_HEIGHTS = {
    "source_jd": 240,
    "manual_jd": 250,
    "resume_editor": 280,
}


def css_variable_block() -> str:
    """把上面的配置转换成网页可使用的 CSS 变量。"""

    variables: list[str] = []
    for settings in (COLORS, SIZES, LANDING, TYPOGRAPHY):
        variables.extend(
            f"--{name.replace('_', '-')}: {value};" for name, value in settings.items()
        )
    return "\n        ".join(variables)
