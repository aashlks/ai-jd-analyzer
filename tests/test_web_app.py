"""Offline checks for the find → shortlist → analyze flow."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from models import JobGroupProfile


APP_FILE = Path(__file__).resolve().parents[1] / "web_app.py"
SAMPLE_JOB = {
    "id": "manual:sample",
    "source": "手动添加",
    "title": "内容运营专员",
    "company": "示例公司",
    "location": "武汉",
    "jd_text": "需要文案写作和活动复盘。",
    "url": "https://example.com/job",
    "original_url": "",
    "published_at": "",
}


class WebAppFlowTests(unittest.TestCase):
    def test_first_page_explains_product_then_opens_job_search(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run()

        self.assertFalse(app.exception)
        self.assertFalse(app.session_state["entered_app"])
        self.assertEqual(app.session_state["active_page"], "找岗位")
        self.assertEqual(len(app.text_area), 0)
        self.assertEqual(len(app.json), 0)
        self.assertIn("别只读一份 JD", " ".join(item.value for item in app.markdown))
        self.assertEqual(len(app.get("popover")), 0)
        self.assertEqual(len(app.get("button_group")), 0)

        next(button for button in app.button if button.label == "进入求职对照台").click().run()
        self.assertTrue(app.session_state["entered_app"])
        self.assertEqual(app.session_state["active_page"], "找岗位")
        self.assertEqual(len(app.text_area), 1)  # Manual JD form is available.
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["自动搜索（Offer岛）", "手动添加 JD"],
        )
        self.assertEqual(
            app.get("button_group")[0].options,
            ["找岗位", "我的岗位", "分析中心"],
        )
        # 桌面端两个入口，手机端一个合并入口；CSS 只显示对应版本。
        self.assertEqual(len(app.get("popover")), 3)

        app.get("button_group")[0].set_value("我的岗位").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_page"], "我的岗位")

    def test_adding_a_job_stays_on_find_page_until_user_opens_shortlist(self) -> None:
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["active_page"] = "找岗位"
        app.run()
        next(widget for widget in app.text_input if widget.label == "公司（可选）").set_value("示例公司")
        app.text_area[0].set_value("岗位名称：内容运营专员\n职责：写文章")
        next(button for button in app.button if button.label == "加入我的岗位").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_page"], "找岗位")
        self.assertEqual(len(app.session_state["saved_jobs"]), 1)
        self.assertEqual(next(iter(app.session_state["saved_jobs"].values()))["company"], "示例公司")
        self.assertIn("添加成功", " ".join(item.value for item in app.get("toast")))
        app.get("button_group")[0].set_value("我的岗位").run()
        self.assertEqual(len(app.checkbox), 1)
        self.assertFalse(app.checkbox[0].value)
        self.assertEqual(app.session_state["chosen_job_ids"], [])
        self.assertEqual(len(app.selectbox), 0)  # Cards, not a hidden dropdown.

    def test_bulk_selection_survives_navigation_without_calling_model(self) -> None:
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["active_page"] = "找岗位"
        app.run()
        app.text_area[0].set_value("岗位名称：内容运营专员\n职责：写文章")
        next(button for button in app.button if button.label == "加入我的岗位").click().run()
        app.get("button_group")[0].set_value("我的岗位").run()
        next(button for button in app.button if button.label == "全选").click().run()
        self.assertTrue(app.checkbox[0].value)
        self.assertEqual(len(app.session_state["chosen_job_ids"]), 1)

        with patch("matcher.match_resume") as model_call:
            next(
                button for button in app.button if button.label == "精读其中一个岗位"
            ).click().run()
            self.assertEqual(app.session_state["active_page"], "分析中心")
            self.assertEqual(app.session_state["analysis_mode"], "单岗位精读")
            self.assertIsNone(app.selectbox[0].value)

            # AppTest's selectbox uses the formatted visible option.
            app.selectbox[0].select(app.selectbox[0].options[0]).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get("file_uploader")), 1)
            self.assertEqual(len(app.session_state["chosen_job_ids"]), 1)
            model_call.assert_not_called()

    def test_select_all_and_select_none_update_every_card(self) -> None:
        another = dict(SAMPLE_JOB)
        another.update(id="manual:another", title="产品助理", jd_text="需要用户访谈。")
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {
            SAMPLE_JOB["id"]: SAMPLE_JOB,
            another["id"]: another,
        }
        app.session_state["active_page"] = "我的岗位"
        app.run()

        self.assertEqual(len(app.checkbox), 2)
        next(button for button in app.button if button.label == "全选").click().run()
        self.assertEqual(len(app.session_state["chosen_job_ids"]), 2)
        self.assertTrue(all(box.value for box in app.checkbox))

        next(button for button in app.button if button.label == "全不选").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["chosen_job_ids"], [])
        self.assertTrue(all(not box.value for box in app.checkbox))

        app.checkbox[1].check().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["chosen_job_ids"], [another["id"]])

    def test_removing_job_also_removes_it_from_analysis_selection(self) -> None:
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {SAMPLE_JOB["id"]: SAMPLE_JOB}
        app.session_state["chosen_job_ids"] = [SAMPLE_JOB["id"]]
        app.session_state["active_page"] = "我的岗位"
        app.run()

        next(button for button in app.button if button.key == "remove-manual:sample").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["saved_jobs"], {})
        self.assertEqual(app.session_state["chosen_job_ids"], [])

    def test_same_jd_text_cannot_be_added_twice(self) -> None:
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {SAMPLE_JOB["id"]: SAMPLE_JOB}
        app.session_state["active_page"] = "找岗位"
        app.run()
        app.text_area[0].set_value("  需要文案写作和活动复盘。  ")
        next(button for button in app.button if button.label == "加入我的岗位").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["saved_jobs"]), 1)
        self.assertIn("已经在列表", " ".join(item.value for item in app.info))

    def test_switching_analysis_target_updates_jd_preview(self) -> None:
        another = dict(SAMPLE_JOB)
        another.update(id="manual:another", title="产品助理", jd_text="需要用户访谈。")
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {
            SAMPLE_JOB["id"]: SAMPLE_JOB,
            another["id"]: another,
        }
        app.session_state["chosen_job_ids"] = [SAMPLE_JOB["id"], another["id"]]
        app.session_state["active_page"] = "分析中心"
        app.session_state["analysis_mode"] = "单岗位精读"
        app.run()

        app.selectbox[0].select(app.selectbox[0].options[0]).run()
        first_preview = next(area for area in app.text_area if area.key.startswith("target-jd-"))
        self.assertEqual(first_preview.value, SAMPLE_JOB["jd_text"])

        app.selectbox[0].select(app.selectbox[0].options[1]).run()
        second_preview = next(area for area in app.text_area if area.key.startswith("target-jd-"))
        self.assertFalse(app.exception)
        self.assertEqual(second_preview.value, another["jd_text"])

    def test_search_can_page_with_the_submitted_keyword(self) -> None:
        first = dict(SAMPLE_JOB)
        first.update(id="offerdao:first", source="Offer岛", title="内容运营", company="甲公司")
        second = dict(SAMPLE_JOB)
        second.update(id="offerdao:second", source="Offer岛", title="活动运营", company="乙公司")

        def fake_search(keyword, *, offset, limit, **kwargs):
            jobs = [first] if offset == 0 else [second]
            return {"items": jobs, "total": 25, "offset": offset, "limit": limit}

        app = AppTest.from_file(str(APP_FILE))
        app.session_state["offerdao_test_key"] = "test-only-key"
        app.session_state["active_page"] = "找岗位"
        with patch("job_sources.search_jobs", side_effect=fake_search) as search:
            app.run()
            next(widget for widget in app.text_input if widget.label == "岗位关键词").set_value("运营")
            next(button for button in app.button if button.label == "搜索岗位").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["search_query"]["keyword"], "运营")
            self.assertEqual(app.session_state["search_results"]["offset"], 0)

            next(button for button in app.button if button.label == "下一页").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["search_results"]["offset"], 20)
            self.assertEqual(search.call_args.args[0], "运营")
            self.assertEqual(search.call_args.kwargs["offset"], 20)
            self.assertEqual(app.session_state["search_results"]["items"][0]["company"], "乙公司")

    def test_offer_single_and_page_add_stay_on_search_page(self) -> None:
        first = dict(SAMPLE_JOB)
        first.update(id="offerdao:first", source="Offer岛", title="内容运营")
        second = dict(SAMPLE_JOB)
        second.update(
            id="offerdao:second",
            source="Offer岛",
            title="活动运营",
            jd_text="负责线下活动执行。",
        )

        def fake_search(keyword, *, offset, limit, **kwargs):
            jobs = [first, second]
            return {"items": jobs, "total": 2, "offset": offset, "limit": limit}

        app = AppTest.from_file(str(APP_FILE))
        app.session_state["offerdao_test_key"] = "test-only-key"
        app.session_state["active_page"] = "找岗位"
        with patch("job_sources.search_jobs", side_effect=fake_search):
            app.run()
            next(widget for widget in app.text_input if widget.label == "岗位关键词").set_value("运营")
            next(button for button in app.button if button.label == "搜索岗位").click().run()
            next(button for button in app.button if button.key == "add-offerdao:first").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["active_page"], "找岗位")
            self.assertEqual(len(app.session_state["saved_jobs"]), 1)
            self.assertIn("添加成功", " ".join(item.value for item in app.get("toast")))

            next(button for button in app.button if button.label == "把本页岗位全部加入我的列表").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["active_page"], "找岗位")
            self.assertEqual(len(app.session_state["saved_jobs"]), 2)
            self.assertIn("已加入 1 个岗位", " ".join(item.value for item in app.get("toast")))

    def test_shortlist_shows_selected_company_diversity(self) -> None:
        another = dict(SAMPLE_JOB)
        another.update(id="manual:another", title="活动运营", company="另一家公司")
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {
            SAMPLE_JOB["id"]: SAMPLE_JOB,
            another["id"]: another,
        }
        app.session_state["chosen_job_ids"] = [SAMPLE_JOB["id"], another["id"]]
        app.session_state["active_page"] = "我的岗位"
        app.run()

        self.assertFalse(app.exception)
        visible_text = " ".join(item.value for item in app.markdown)
        self.assertIn("这组样本：2 条岗位 · 2 家已知公司", visible_text)
        self.assertIn("公司分布：", " ".join(item.value for item in app.get("caption")))
        self.assertIn("少于 5 条", " ".join(item.value for item in app.info))

    def test_group_analysis_is_explicit_and_renders_readable_profile(self) -> None:
        another = dict(SAMPLE_JOB)
        another.update(
            id="manual:another",
            title="活动运营",
            company="另一家公司",
            jd_text="负责活动策划和数据复盘。",
        )
        profile = JobGroupProfile.model_validate(
            {
                "direction_name": "内容与活动运营",
                "summary": "这组样本关注内容、活动和复盘。",
                "consistency_summary": "两条岗位方向大体一致。",
                "job_ids": [SAMPLE_JOB["id"], another["id"]],
                "outlier_job_ids": [],
                "signals": [
                    {
                        "label": "活动复盘",
                        "category": "专业能力",
                        "evidence": [
                            {"job_id": SAMPLE_JOB["id"], "quote": "活动复盘"},
                            {"job_id": another["id"], "quote": "数据复盘"},
                        ],
                    }
                ],
            }
        )
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {
            SAMPLE_JOB["id"]: SAMPLE_JOB,
            another["id"]: another,
        }
        app.session_state["chosen_job_ids"] = [SAMPLE_JOB["id"], another["id"]]
        app.session_state["active_page"] = "我的岗位"

        with patch("group_analyzer.analyze_job_group", return_value=profile) as model_call:
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-only-key"}):
                app.run()
                next(
                    button for button in app.button if button.label.startswith("分析岗位方向")
                ).click().run()
                self.assertEqual(app.session_state["active_page"], "分析中心")
                self.assertEqual(app.session_state["analysis_mode"], "岗位方向画像")
                model_call.assert_not_called()

                next(
                    box for box in app.checkbox if "我已核对以上" in box.label
                ).check().run()
                next(
                    button for button in app.button if button.label == "生成岗位方向画像"
                ).click().run()

        self.assertFalse(app.exception)
        model_call.assert_called_once()
        self.assertEqual(app.session_state["model_request_count"], 1)
        visible_text = " ".join(item.value for item in app.markdown)
        self.assertIn("内容与活动运营", " ".join(item.value for item in app.subheader))
        self.assertIn("活动复盘", visible_text)
        self.assertEqual(len(app.json), 0)

    def test_model_request_limit_blocks_group_api_call(self) -> None:
        another = dict(SAMPLE_JOB)
        another.update(
            id="manual:another",
            title="活动运营",
            company="另一家公司",
            jd_text="负责活动策划和数据复盘。",
        )
        app = AppTest.from_file(str(APP_FILE))
        app.session_state["saved_jobs"] = {
            SAMPLE_JOB["id"]: SAMPLE_JOB,
            another["id"]: another,
        }
        app.session_state["chosen_job_ids"] = [SAMPLE_JOB["id"], another["id"]]
        app.session_state["active_page"] = "分析中心"
        app.session_state["analysis_mode"] = "岗位方向画像"
        app.session_state["model_request_count"] = 99

        with patch("group_analyzer.analyze_job_group") as model_call:
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-only-key"}):
                app.run()
                next(
                    box for box in app.checkbox if "我已核对以上" in box.label
                ).check().run()
                next(
                    button for button in app.button if button.label == "生成岗位方向画像"
                ).click().run()

        self.assertFalse(app.exception)
        model_call.assert_not_called()
        self.assertIn("已达到", " ".join(item.value for item in app.error))
        self.assertEqual(app.session_state["group_profiles"], {})


if __name__ == "__main__":
    unittest.main()
