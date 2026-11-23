#!/usr/bin/env python3
# encoding=utf-8
import unittest
from unittest.mock import MagicMock, patch

from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException

import captcha_assist
import chrome_tixcraft as bot


class CaptchaAssistTests(unittest.TestCase):
    def test_capture_returns_png_bytes(self):
        driver = MagicMock()
        image = driver.find_element.return_value
        image.screenshot_as_png = b"png-data"

        self.assertEqual(captcha_assist.capture_captcha_image(driver), b"png-data")
        driver.execute_script.assert_called_once()

    def test_capture_returns_none_when_image_is_missing(self):
        driver = MagicMock()
        driver.find_element.side_effect = NoSuchElementException()

        self.assertIsNone(captcha_assist.capture_captcha_image(driver))
        self.assertEqual(driver.find_element.call_count, len(captcha_assist.CAPTCHA_IMAGE_SELECTORS))

    def test_capture_uses_next_selector_after_empty_screenshot(self):
        driver = MagicMock()
        empty_image = MagicMock()
        empty_image.screenshot_as_png = b""
        usable_image = MagicMock()
        usable_image.screenshot_as_png = b"png-data"
        driver.find_element.side_effect = [empty_image, usable_image]

        self.assertEqual(captcha_assist.capture_captcha_image(driver), b"png-data")
        self.assertEqual(driver.find_element.call_count, 2)

    @patch("captcha_assist._prompt_with_tk", return_value="  AB12  ")
    def test_prompt_returns_stripped_text(self, prompt):
        self.assertEqual(captcha_assist.prompt_user_for_code(b"image", 60), "AB12")
        prompt.assert_called_once_with(b"image", 60)

    @patch("captcha_assist._prompt_with_cli")
    @patch("captcha_assist._prompt_with_tk", return_value=None)
    def test_prompt_returns_none_on_timeout(self, tk_prompt, cli_prompt):
        # The Tk window returns None when its countdown expires.
        self.assertIsNone(captcha_assist.prompt_user_for_code(b"image", 1))
        tk_prompt.assert_called_once_with(b"image", 1)
        cli_prompt.assert_not_called()

    @patch("captcha_assist._read_cli_line", return_value="  xy9  ")
    @patch("captcha_assist._prompt_with_tk", side_effect=RuntimeError("no display"))
    def test_prompt_cli_fallback_returns_stripped_text(self, tk_prompt, read_line):
        self.assertEqual(captcha_assist.prompt_user_for_code(b"image", 5), "xy9")
        read_line.assert_called_once_with(5)

    @patch("captcha_assist._prompt_with_cli", return_value=None)
    @patch("captcha_assist._prompt_with_tk", side_effect=RuntimeError("no display"))
    def test_prompt_returns_none_on_fallback_cancel(self, tk_prompt, cli_prompt):
        self.assertIsNone(captcha_assist.prompt_user_for_code(b"image", 1))
        tk_prompt.assert_called_once_with(b"image", 1)
        cli_prompt.assert_called_once_with(b"image", 1)

    @unittest.skipIf(captcha_assist.os.name == "nt", "POSIX terminal behavior")
    def test_cli_read_honors_timeout(self):
        with patch("captcha_assist.select.select", return_value=([], [], [])) as wait_for_input:
            self.assertIsNone(captcha_assist._read_cli_line(7))
        wait_for_input.assert_called_once_with([captcha_assist.sys.stdin], [], [], 7)

    @unittest.skipIf(captcha_assist.os.name == "nt", "POSIX terminal behavior")
    def test_cli_read_returns_available_line(self):
        stdin = MagicMock()
        stdin.readline.return_value = "AB12\n"
        with patch.object(captcha_assist.sys, "stdin", stdin), patch(
            "captcha_assist.select.select", return_value=([stdin], [], [])
        ):
            self.assertEqual(captcha_assist._read_cli_line(5), "AB12\n")

    def test_fill_returns_true_when_value_matches(self):
        driver = MagicMock()
        verify_input = driver.find_element.return_value
        verify_input.get_attribute.return_value = "AB12"

        self.assertTrue(captcha_assist.fill_captcha(driver, "AB12"))
        verify_input.clear.assert_called_once_with()
        verify_input.send_keys.assert_called_once_with("AB12")

    def test_capture_prefers_canvas_data_url_when_available(self):
        driver = MagicMock()
        driver.execute_script.return_value = "data:image/png;base64,cG5nLWNhbnZhcw=="

        self.assertEqual(captcha_assist.capture_captcha_image(driver), b"png-canvas")
        driver.execute_script.assert_called_once()

    def test_fill_falls_back_to_js_when_click_intercepted(self):
        driver = MagicMock()
        verify_input = driver.find_element.return_value
        verify_input.click.side_effect = ElementClickInterceptedException("banner overlay")
        verify_input.get_attribute.return_value = "AB12"

        self.assertTrue(captcha_assist.fill_captcha(driver, "AB12"))
        driver.execute_script.assert_called_once()

    def test_fill_returns_false_when_value_differs(self):
        driver = MagicMock()
        driver.find_element.return_value.get_attribute.return_value = "AB1"

        self.assertFalse(captcha_assist.fill_captcha(driver, "AB12"))

    @patch("captcha_assist.time.sleep")
    @patch("captcha_assist.fill_captcha", return_value=False)
    @patch("captcha_assist.prompt_user_for_code", return_value="AB12")
    @patch("captcha_assist.capture_captcha_image", return_value=b"image")
    def test_retry_loop_stops_at_max_retries(self, capture, prompt, fill, sleep):
        assist = captcha_assist.CaptchaAssist(timeout_s=10, max_retries=3)

        self.assertFalse(assist.run(MagicMock()))
        self.assertEqual(capture.call_count, 3)
        self.assertEqual(prompt.call_count, 3)
        self.assertEqual(fill.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("captcha_assist.fill_captcha")
    @patch("captcha_assist.prompt_user_for_code", return_value=None)
    @patch("captcha_assist.capture_captcha_image", return_value=b"image")
    def test_user_cancel_stops_without_retrying_or_filling(self, capture, prompt, fill):
        assist = captcha_assist.CaptchaAssist(timeout_s=10, max_retries=3)
        driver = MagicMock()

        self.assertFalse(assist.run(driver))
        capture.assert_called_once_with(driver)
        prompt.assert_called_once_with(b"image", 10)
        fill.assert_not_called()

    @patch("chrome_tixcraft._run_captcha_assist", return_value=True)
    @patch("chrome_tixcraft.ticket_number_auto_fill")
    @patch("chrome_tixcraft.Select")
    def test_purchase_flow_runs_assist_when_enabled(self, select_class, ticket_fill, run_assist):
        driver = MagicMock()
        form_select = driver.find_element.return_value
        selected_option = MagicMock()
        selected_option.text = "0"
        selected_option.get_attribute.return_value = "0"
        select_class.return_value.first_selected_option = selected_option

        with patch.object(bot, "driver", driver), patch.object(bot, "captcha_assist_enabled", True), patch.object(bot, "auto_press_confirm_button_enabled", False):
            self.assertTrue(bot.tixcraft_ticket_main("https://tixcraft.com/ticket/ticket/demo", False))

        ticket_fill.assert_called_once_with("https://tixcraft.com/ticket/ticket/demo", form_select)
        run_assist.assert_called_once_with(driver)

    @patch("chrome_tixcraft.CaptchaAssist")
    def test_feature_is_skipped_when_disabled(self, assist_class):
        with patch.object(bot, "captcha_assist_enabled", False), patch.object(bot, "captcha_auto_ocr_enabled", False):
            self.assertIsNone(bot._run_captcha_assist(MagicMock()))
        assist_class.assert_not_called()

    def test_normalize_code_filters_and_preserves_case(self):
        self.assertEqual(captcha_assist._normalize_code("  aB12 "), "aB12")
        self.assertEqual(captcha_assist._normalize_code("A1b2C3"), "A1b2C3")
        self.assertIsNone(captcha_assist._normalize_code("abc"))
        self.assertIsNone(captcha_assist._normalize_code("abcdefg"))
        self.assertIsNone(captcha_assist._normalize_code(""))
        self.assertIsNone(captcha_assist._normalize_code(None))

    def test_recognize_captcha_returns_normalized_code(self):
        engine = MagicMock()
        engine.classification.return_value = "aB12"

        self.assertEqual(captcha_assist.recognize_captcha(b"image", engine=engine), "aB12")

    def test_recognize_captcha_tries_variants_until_valid(self):
        engine = MagicMock()
        engine.classification.side_effect = ["??", "aB12"]

        with patch("captcha_assist._preprocess_variants", return_value=[b"v1", b"v2"]):
            self.assertEqual(captcha_assist.recognize_captcha(b"image", engine=engine), "aB12")
        self.assertEqual(engine.classification.call_count, 2)

    def test_recognize_captcha_returns_none_when_engine_missing(self):
        with patch("captcha_assist._get_ocr_engine", return_value=(None, RuntimeError("no ddddocr"))):
            self.assertIsNone(captcha_assist.recognize_captcha(b"image"))

    def test_recognize_captcha_returns_none_when_all_variants_invalid(self):
        engine = MagicMock()
        engine.classification.side_effect = ["!!!", "???"]
        with patch("captcha_assist._preprocess_variants", return_value=[b"v1", b"v2"]):
            self.assertIsNone(captcha_assist.recognize_captcha(b"image", engine=engine))

    @patch("captcha_assist.fill_captcha", return_value=True)
    @patch("captcha_assist.prompt_user_for_code")
    @patch("captcha_assist.recognize_captcha", return_value="AB12")
    @patch("captcha_assist.capture_captcha_image", return_value=b"image")
    def test_run_uses_ocr_without_prompting_when_recognized(self, capture, recognize, prompt, fill):
        assist = captcha_assist.CaptchaAssist(timeout_s=10, max_retries=3, auto_ocr=True, prompt_enabled=True)

        self.assertTrue(assist.run(MagicMock()))
        recognize.assert_called_once_with(b"image")
        prompt.assert_not_called()
        fill.assert_called_once()

    @patch("captcha_assist.fill_captcha", return_value=True)
    @patch("captcha_assist.prompt_user_for_code", return_value="MANUAL")
    @patch("captcha_assist.recognize_captcha", return_value=None)
    @patch("captcha_assist.capture_captcha_image", return_value=b"image")
    def test_run_falls_back_to_prompt_when_ocr_fails(self, capture, recognize, prompt, fill):
        assist = captcha_assist.CaptchaAssist(timeout_s=10, max_retries=3, auto_ocr=True, prompt_enabled=True)

        self.assertTrue(assist.run(MagicMock()))
        prompt.assert_called_once_with(b"image", 10)


if __name__ == "__main__":
    unittest.main()
