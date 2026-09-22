"""集中管理 Streamlit 网页的外观。

这里没有岗位、简历或 API 逻辑。修改数值并保存后，欢迎页和主工作区会一起更新。
CSS 尺寸要保留 ``px``、``rem`` 或 ``vw`` 等单位。
"""


# 像一本可核对原文的求职研究手册：纸张承载长文本，墨色保证阅读，
# 松绿表示已确认的岗位信号，赭色提示来源与注释。
COLORS = {
    "ink": "#243733",
    "muted": "#5f6f69",
    "signal": "#31766b",
    "signal_dark": "#195b52",
    "signal_pale": "#e4f0e8",
    "signal_mist": "#f0f5ee",
    "annotation": "#a65d3b",
    "annotation_pale": "#f9eee5",
    "line": "#d5dcd3",
    "paper": "#fffefa",
    "canvas": "#f6f5ef",
    "landing_canvas": "#eeeee4",
}


# 工作区通用尺寸：集中控制页面宽度、留白、卡片和按钮，不用去 web_app.py 到处找数字。
SIZES = {
    "app_max_width": "1180px",
    "app_top_padding": "1.45rem",
    "app_bottom_padding": "3.5rem",
    "header_min_height": "3.2rem",
    "section_gap": "1.35rem",
    "panel_radius": "12px",
    "panel_padding": "1.2rem",
    "panel_shadow": "0 10px 28px rgba(38, 60, 49, 0.045)",
    "button_height": "2.7rem",
    "button_radius": "7px",
    "input_radius": "7px",
    "metric_radius": "10px",
    "page_intro_padding": "1.65rem 2rem",
    "page_intro_radius": "12px",
    "page_title_size": "clamp(2rem, 3.7vw, 3.15rem)",
    "page_copy_width": "720px",
}


# 独立欢迎页尺寸：只影响用户首次进入时看到的全屏页面。
LANDING = {
    "landing_max_width": "1240px",
    "landing_min_height": "100vh",
    "landing_outer_padding": "clamp(1.25rem, 4vw, 3.5rem)",
    "landing_hero_padding": "clamp(1.7rem, 5vw, 4.5rem)",
    "landing_hero_radius": "16px",
    "landing_title_size": "clamp(3rem, 5.8vw, 5.8rem)",
    "landing_title_width": "720px",
    "landing_copy_width": "570px",
    "landing_cta_width": "240px",
    "landing_feature_radius": "10px",
    "landing_feature_min_height": "150px",
}


TYPOGRAPHY = {
    "body_font": '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
    "display_font": '"Iowan Old Style", "Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", Georgia, serif',
    "mono_font": '"IBM Plex Mono", "Cascadia Code", Consolas, monospace',
    "body_size": "16px",
    "small_size": ".88rem",
    "body_line_height": "1.7",
}


# 各区块横向比例：只改数字即可；数字越大，对应列分到的空间越多。
COLUMN_RATIOS = {
    "landing_hero": [1.35, 1],
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
